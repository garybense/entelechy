import time
import uuid
import logging
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
import json

from entelechy_api.models import RequestContext

def get_request_context(authorization: str | None = Header(default=None)) -> RequestContext:
    """
    Extract request context from Authorization header.
    """
    api_key = None
    if authorization:
        if authorization.lower().startswith("bearer "):
            api_key = authorization[7:].strip()
        else:
            api_key = authorization.strip()
    return RequestContext(api_key=api_key)

from entelechy_api.api.openai_schemas import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice,
    ChatCompletionMessage, ChatCompletionUsage, ChatCompletionStreamResponse,
    ChatCompletionStreamChoice
)

logger = logging.getLogger(__name__)

router = APIRouter()

async def resolve_bank_id(memory: Any, model_name: str, request_context: RequestContext) -> str:
    """Resolve the bank ID from the model name."""
    # Try direct match
    try:
        await memory.get_bank_profile(model_name, request_context=request_context)
        return model_name
    except Exception:
        # If not direct match, list banks and pick the first one as default if model is "default" or "gpt-..."
        banks = await memory.list_banks(request_context=request_context)
        if not banks:
            raise HTTPException(status_code=404, detail="No banks found")
        
        # If model_name is "default" or empty, return the first bank
        if model_name in ["default", "", "entelechy"]:
            return banks[0]["bank_id"]
            
        # Check if model_name matches any bank name (case-insensitive)
        for bank in banks:
            if bank.get("name", "").lower() == model_name.lower():
                return bank["bank_id"]
        
        # If no match, return the first bank as fallback (Grok behavior)
        return banks[0]["bank_id"]

@router.get("/models")
@router.get("/v1/models")
async def list_models(
    raw_request: Request,
    request_context: RequestContext = Depends(get_request_context)
):
    memory = raw_request.app.state.memory
    try:
        banks = await memory.list_banks(request_context=request_context)
        return {
            "object": "list",
            "data": [
                {
                    "id": bank["bank_id"],
                    "object": "model",
                    "created": int(bank["created_at"].timestamp()) if bank.get("created_at") else int(time.time()),
                    "owned_by": "entelechy"
                }
                for bank in banks
            ]
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/completions")
@router.get("/v1/chat/completions")
async def openai_chat_completions_get():
    return {"status": "ok", "message": "Entelechy OpenAI-compatible endpoint is active. Please use POST for chat completions."}

@router.post("/chat/completions")
@router.post("/v1/chat/completions")
async def openai_chat_completions(
    request: ChatCompletionRequest,
    raw_request: Request,
    request_context: RequestContext = Depends(get_request_context)
):
    memory = raw_request.app.state.memory
    
    # 1. Resolve bank_id
    bank_id = await resolve_bank_id(memory, request.model, request_context)
    
    # 2. Build query and context from messages
    # We use the full message history as context for the reflection
    history = []
    query = ""
    for msg in request.messages:
        if msg.role == "user":
            query = msg.content or ""
            history.append(f"User: {query}")
        elif msg.role == "assistant":
            history.append(f"Assistant: {msg.content or ''}")
        elif msg.role == "system":
            history.append(f"System: {msg.content or ''}")
            
    context = "\n".join(history[:-1]) if len(history) > 1 else None
    
    # 3. Handle Streaming
    if request.stream:
        return StreamingResponse(
            openai_stream_generator(memory, bank_id, query, context, request, request_context),
            media_type="text/event-stream"
        )
    
    # 4. Non-streaming call
    try:
        core_result = await memory.reflect_async(
            bank_id=bank_id,
            query=query,
            context=context,
            request_context=request_context,
            max_tokens=request.max_tokens or 4096,
        )
        
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=core_result.text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=core_result.usage.input_tokens if core_result.usage else 0,
                completion_tokens=core_result.usage.output_tokens if core_result.usage else 0,
                total_tokens=core_result.usage.total_tokens if core_result.usage else 0
            )
        )
        return response
    except Exception as e:
        logger.error(f"Error in reflect_async: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def openai_stream_generator(memory: Any, bank_id: str, query: str, context: Optional[str], request: ChatCompletionRequest, request_context: RequestContext):
    """Generator for OpenAI-compatible streaming responses."""
    request_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(time.time())
    
    try:
        # Since reflect_async doesn't stream yet, we do the full call and then stream the result
        # This still provides the 'stream' interface but without intermediate chunks from the LLM.
        # In a future update, we can modify MemoryEngine to support streaming.
        core_result = await memory.reflect_async(
            bank_id=bank_id,
            query=query,
            context=context,
            request_context=request_context,
            max_tokens=request.max_tokens or 4096,
        )
        
        # Stream the content in chunks to simulate real streaming
        content = core_result.text
        chunk_size = 20 # characters per chunk
        for i in range(0, len(content), chunk_size):
            chunk_text = content[i:i+chunk_size]
            chunk_resp = ChatCompletionStreamResponse(
                id=request_id,
                created=created,
                model=request.model,
                choices=[
                    ChatCompletionStreamChoice(
                        index=0,
                        delta=ChatCompletionMessage(role="assistant", content=chunk_text),
                        finish_reason=None
                    )
                ]
            )
            yield f"data: {chunk_resp.model_dump_json()}\n\n"
            
        # Final chunk
        final_chunk = ChatCompletionStreamResponse(
            id=request_id,
            created=created,
            model=request.model,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta=ChatCompletionMessage(role="assistant", content=""),
                    finish_reason="stop"
                )
            ]
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in stream generator: {e}")
        error_resp = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "param": None,
                "code": None
            }
        }
        yield f"data: {json.dumps(error_resp)}\n\n"
        yield "data: [DONE]\n\n"
