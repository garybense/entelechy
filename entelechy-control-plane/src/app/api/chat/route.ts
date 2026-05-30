import { NextResponse } from 'next/server';
import { streamText } from 'ai';
import { createVertex } from '@ai-sdk/google-vertex';

export async function POST(req: Request) {
  try {
    const { messages, bankId } = await req.json();

    if (!bankId) {
      return NextResponse.json({ error: 'bankId is required' }, { status: 400 });
    }

    // Set credentials environment explicitly for Vertex AI so it doesn't need manual config
    process.env.GOOGLE_APPLICATION_CREDENTIALS = "/mnt/data/code/entelechy/service-account-key.json";

    const vertex = createVertex({
      project: 'project-d8dbd49b-d7de-411e-824',
      location: 'global', // Try us-east1, global often throws errors in the Vercel SDK
    });

    // 1. Call Entelechy /bootstrap silently
    let systemPromptOverride = "You are a helpful assistant.";
    
    try {
      const userPrompt = messages[messages.length - 1].content;
      // Fetch from local Entelechy API
      const bootstrapRes = await fetch(`http://localhost:8888/v1/default/banks/${bankId}/sessions/bootstrap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          svt: 'CST-simulator',
          context: userPrompt
        })
      });

      if (bootstrapRes.ok) {
        const bootstrapData = await bootstrapRes.json();
        systemPromptOverride = bootstrapData.injected_prompt || systemPromptOverride;
      } else {
        console.error("Bootstrap failed", await bootstrapRes.text());
      }
    } catch (e) {
      console.error("Error calling Entelechy bootstrap", e);
    }

    // 2. Call LLM using Vercel AI SDK (Vertex AI Gemini)
    const result = streamText({
      model: vertex('gemini-3.1-pro-preview'), // standard pro model
      system: systemPromptOverride,
      messages,
      onFinish: async (completionResult) => {
        // 3. Auto-Retain Background Task (The interception)
        try {
          const userPrompt = messages[messages.length - 1].content;
          const agentResponse = completionResult.text;
          
          await fetch(`http://localhost:8888/v1/default/memories/retain_async`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              bank_id: bankId,
              context: 'chat_simulator',
              content: `[EXPERIENCE] User asked: "${userPrompt}". Assistant responded: "${agentResponse}".`
            })
          });
          console.log("Auto-retained conversation to Entelechy.");
        } catch (e) {
          console.error("Auto-retain failed", e);
        }
      }
    });

    return result.toUIMessageStreamResponse();
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
