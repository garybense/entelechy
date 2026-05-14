from typing import Any, Literal, Optional, Union, List
from pydantic import BaseModel, Field

class ChatCompletionMessage(BaseModel):
    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

class ChatCompletionToolFunction(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: dict[str, Any]

class ChatCompletionTool(BaseModel):
    type: Literal["function"]
    function: ChatCompletionToolFunction

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    tools: Optional[List[ChatCompletionTool]] = None
    tool_choice: Optional[Union[str, dict[str, Any]]] = "auto"
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[dict[str, float]] = None
    user: Optional[str] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None

class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None

class ChatCompletionStreamChoice(BaseModel):
    index: int
    delta: ChatCompletionMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]
