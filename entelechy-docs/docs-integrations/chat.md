---
sidebar_position: 5
title: "Vercel Chat SDK Persistent Memory with Entelechy | Integration"
description: "Give your Vercel Chat SDK bot persistent, per-user memory across Slack, Discord, Teams, and more. Single handler wrapper, no custom plumbing required."
---

# Vercel Chat SDK

We built `@garybense/entelechy-chat` to give [Vercel Chat SDK](https://github.com/vercel/chat) bots persistent, per-user memory with a single handler wrapper. The integration works across Slack, Discord, Teams, Google Chat, GitHub, and Linear — no custom plumbing required.

[View Changelog →](/changelog/integrations/chat)

## Installation

```bash
npm install @garybense/entelechy-chat
```

## Quick Start

```typescript
import { Chat } from 'chat';
import { EntelechyClient } from '@garybense/entelechy-client';
import { withEntelechyChat } from '@garybense/entelechy-chat';
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const chat = new Chat({ connectors: [/* your connectors */] });
const entelechy = new EntelechyClient({ apiKey: process.env.ENTELECHY_API_KEY });

chat.onNewMention(
  withEntelechyChat(
    {
      client: entelechy,
      bankId: (msg) => msg.author.userId, // per-user memory
    },
    async (thread, message, ctx) => {
      await thread.subscribe();

      const result = await streamText({
        model: openai('gpt-4o'),
        system: ctx.memoriesAsSystemPrompt(),
        messages: [{ role: 'user', content: message.text }],
      });

      // Stream the response
      const chunks: string[] = [];
      for await (const chunk of result.textStream) {
        chunks.push(chunk);
      }
      const fullResponse = chunks.join('');
      await thread.post(fullResponse);

      // Store the conversation in memory
      await ctx.retain(
        `User: ${message.text}\nAssistant: ${fullResponse}`
      );
    }
  )
);
```

## Configuration

### `withEntelechyChat(options, handler)`

`withEntelechyChat` wraps your existing Chat SDK handler and injects memory context automatically. It returns a standard handler `(thread, message) => Promise<void>` so it drops in without changing your handler signature.

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `client` | `EntelechyClient` | *required* | Entelechy client instance |
| `bankId` | `string \| (msg) => string` | *required* | Memory bank ID or resolver function |
| `recall.enabled` | `boolean` | `true` | Auto-recall memories before handler |
| `recall.budget` | `'low' \| 'mid' \| 'high'` | `'mid'` | Processing budget for recall |
| `recall.maxTokens` | `number` | API default | Max tokens for recall results |
| `recall.types` | `FactType[]` | all | Filter to specific fact types |
| `recall.includeEntities` | `boolean` | `true` | Include entity observations |
| `retain.enabled` | `boolean` | `false` | Auto-retain inbound messages |
| `retain.async` | `boolean` | `true` | Fire-and-forget retain |
| `retain.tags` | `string[]` | – | Tags for retained memories |
| `retain.metadata` | `Record<string, string>` | – | Metadata for retained memories |

### Context (`ctx`)

We inject a third `ctx` argument into your handler that exposes the full Entelechy memory API scoped to the current user's bank:

| Property/Method | Description |
|----------------|-------------|
| `ctx.bankId` | Resolved bank ID |
| `ctx.memories` | Array of recalled memories |
| `ctx.entities` | Entity observations (or null) |
| `ctx.memoriesAsSystemPrompt(options?)` | Format memories for LLM system prompt |
| `ctx.retain(content, options?)` | Store content in memory |
| `ctx.recall(query, options?)` | Search memories |
| `ctx.reflect(query, options?)` | Reason over memories |

## Examples

### Subscribed Message Handler

```typescript
chat.onSubscribedMessage(
  withEntelechyChat(
    {
      client: entelechy,
      bankId: (msg) => msg.author.userId,
      recall: { budget: 'high', maxTokens: 1000 },
    },
    async (thread, message, ctx) => {
      const result = await generateText({
        model: openai('gpt-4o'),
        system: ctx.memoriesAsSystemPrompt(),
        messages: [{ role: 'user', content: message.text }],
      });
      await thread.post(result.text);
    }
  )
);
```

### Auto-Retain Inbound Messages

```typescript
chat.onNewMention(
  withEntelechyChat(
    {
      client: entelechy,
      bankId: (msg) => msg.author.userId,
      retain: { enabled: true, tags: ['slack', 'inbound'] },
    },
    async (thread, message, ctx) => {
      // Inbound message is already being retained automatically
      const result = await generateText({
        model: openai('gpt-4o'),
        system: ctx.memoriesAsSystemPrompt(),
        messages: [{ role: 'user', content: message.text }],
      });
      await thread.post(result.text);

      // Retain the assistant response separately
      await ctx.retain(`Assistant: ${result.text}`, {
        tags: ['slack', 'outbound'],
      });
    }
  )
);
```

### Static Bank ID (Shared Memory)

```typescript
// All users share the same memory bank
chat.onNewMention(
  withEntelechyChat(
    { client: entelechy, bankId: 'shared-team-memory' },
    async (thread, message, ctx) => {
      // ...
    }
  )
);
```

## Error Handling

We designed the integration so that memory failures never break your bot. Auto-recall and auto-retain errors are caught internally, logged as warnings, and the handler continues with empty memories. Manual `ctx.retain()`, `ctx.recall()`, and `ctx.reflect()` calls propagate errors normally so you can handle them as needed.
