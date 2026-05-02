---
sidebar_position: 15
---

# Entelechy AI SDK - Personal Chef


:::info Complete Application
This is a complete, runnable application demonstrating Entelechy integration.
[**View source on GitHub →**](https://github.com/vectorize-io/entelechy-cookbook/tree/main/applications/taste-ai)
:::


A personal food assistant demonstrating three key Entelechy integrations using the [Vercel AI SDK v6](https://sdk.vercel.ai/docs).

## Architecture: Single Bank with User Tags

This demo uses a **single Entelechy bank** (`taste-ai`) for all users, with each user's data tagged using `user:${username}`.

```typescript
// All users share the same bank
const BANK_ID = 'taste-ai';

// Each memory is tagged with the user
await entelechyTools.retain.execute({
  bankId: BANK_ID,
  content: userData,
  tags: [`user:${username}`],
});
```

This architecture enables:
- **Per-user queries**: Filter by `user:alice` to get personalized results
- **Aggregated insights**: Query across all users to find popular recipes or common dietary patterns
- **Simplified management**: One bank to maintain instead of per-user banks

## Three Entelechy Integrations

### 1. Meal Suggestions with Memory Recall & Reflection

Uses `recall` and `reflect` tools with AI SDK's agent-based approach to gather personalized context.

```typescript
const contextResult = await generateText({
  model: llmModel,
  tools: {
    recall: entelechyTools.recall,
    reflect: entelechyTools.reflect,
  },
  toolChoice: 'auto',
  prompt: `You are gathering context for personalized ${mealType} recipe suggestions.

Use the recall tool to search for the user's food preferences, dislikes, and recent meals.
Then use the reflect tool to analyze their dietary patterns and restrictions.

After gathering context, summarize their preferences and recent eating patterns.`,
});
```

The AI agent autonomously:
- Searches memory for cuisine preferences and dietary restrictions
- Analyzes recent protein consumption for variety
- Identifies foods to avoid

### 2. Goal Progress Tracking with Mental Models

Uses mental models to automatically maintain updated insights about user progress.

```typescript
// Create a mental model that auto-refreshes after new meals
await entelechyTools.createMentalModel.execute({
  bankId: BANK_ID,
  mentalModelId: getMentalModelId(username, 'goals'),
  name: `${username}'s Goal Progress`,
  sourceQuery: `Analyze ${username}'s dietary goals and eating patterns.
    Describe their progress towards their stated goals (weight loss, muscle gain, etc.).`,
  tags: [`user:${username}`],
  autoRefresh: true, // Refreshes automatically after consolidation
});

// Query the mental model for current insights
const result = await entelechyTools.queryMentalModel.execute({
  bankId: BANK_ID,
  mentalModelId: mentalModelId,
});
```

Mental models automatically:
- Track progress towards dietary goals
- Update after each new meal is logged
- Provide fresh insights without manual refresh

### 3. Language Enforcement with Directives

Uses directives to ensure all responses match user's language preference.

```typescript
await entelechyClient.createDirective(BANK_ID, {
  name: `${username}'s Language Preference`,
  content: `Always respond in ${language}. All suggestions must be in ${language}.`,
  priority: 100,
  tags: [`user:${username}`, 'directive:language'],
});
```

Directives are automatically injected when mental models generate insights, ensuring consistent language across all interactions.

## Running the Demo

```bash
npm install
npm run dev
```

**Requirements:**
- Entelechy server running at `http://localhost:8888` (or set `ENTELECHY_URL`)
- Node.js 18+

## Learn More

- [Entelechy AI SDK on npm](https://www.npmjs.com/package/@vectorize-io/entelechy-ai-sdk)
- [AI SDK Documentation](https://sdk.vercel.ai/docs)
