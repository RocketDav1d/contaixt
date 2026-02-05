import { streamText } from "ai";
import { createOpenAI } from "@ai-sdk/openai";

export const maxDuration = 60;

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WORKSPACE_ID = "50926c1f-8132-4694-bd8a-b250c4a67089"; // TODO: Get from user session

interface BackendContext {
  chunks: Array<{
    chunk_id: string;
    document_id: string;
    text: string;
    doc_title: string | null;
    doc_url: string | null;
    doc_source_type: string | null;
  }>;
  facts: Array<{
    from_name: string;
    relation: string;
    to_name: string;
    evidence: string | null;
  }>;
  seed_entities: Array<{ key: string; type: string; name: string }>;
}

// Create OpenAI client - uses OPENAI_API_KEY env var
const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const SYSTEM_PROMPT = `You are a knowledge assistant for Contaixt. Answer the user's question using ONLY the provided context.

Context consists of:
1. CHUNKS: Relevant text excerpts from documents (each has a chunk_id)
2. FACTS: Knowledge graph relationships between entities

Rules:
- Only use information present in the context. Do not use prior knowledge.
- If the context doesn't contain enough information, say so honestly.
- When you use information from a chunk, cite it naturally in your response.
- Be concise and direct.
- Answer in the same language as the user's question.
- Format your response in markdown for readability.`;

function buildContextPrompt(context: BackendContext): string {
  const parts: string[] = [];

  if (context.chunks && context.chunks.length > 0) {
    parts.push("=== DOCUMENT EXCERPTS ===");
    for (const c of context.chunks) {
      const title = c.doc_title || "untitled";
      const source = c.doc_source_type || "unknown";
      parts.push(`[${c.chunk_id}] (source: ${source}, doc: ${title})`);
      parts.push(c.text);
      parts.push("");
    }
  }

  if (context.facts && context.facts.length > 0) {
    parts.push("=== KNOWLEDGE GRAPH FACTS ===");
    for (const f of context.facts) {
      const evidence = f.evidence ? ` (evidence: ${f.evidence.slice(0, 100)})` : "";
      parts.push(`- ${f.from_name} --[${f.relation}]--> ${f.to_name}${evidence}`);
    }
    parts.push("");
  }

  return parts.join("\n");
}

// Extract text from a message that might have content string or parts array
function extractMessageText(message: { content?: string; parts?: Array<{ type: string; text?: string }> }): string {
  if (typeof message.content === "string") {
    return message.content;
  }
  if (message.parts) {
    return message.parts
      .filter((part) => part.type === "text" && part.text)
      .map((part) => part.text)
      .join("");
  }
  return "";
}

export async function POST(req: Request) {
  const { messages, vaultIds } = await req.json();

  // Get the last user message
  const lastMessage = messages[messages.length - 1];
  const userPrompt = extractMessageText(lastMessage);

  try {
    // First, get context from our backend
    const contextResponse = await fetch(`${BACKEND_URL}/v1/context`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: WORKSPACE_ID,
        prompt: userPrompt,
        vault_ids: vaultIds || null,
        top_k: 10,
      }),
    });

    let contextText = "";

    if (contextResponse.ok) {
      const context: BackendContext = await contextResponse.json();
      contextText = buildContextPrompt(context);
    }

    // If no context found, provide a helpful message
    if (!contextText) {
      contextText = "No relevant documents found in the knowledge base.";
    }

    // Stream response using OpenAI through AI SDK
    const result = streamText({
      model: openai("gpt-4o-mini"),
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: "user",
          content: `Context:\n${contextText}\n\nQuestion: ${userPrompt}`,
        },
      ],
    });

    // Return streaming response for useChat
    return result.toUIMessageStreamResponse();
  } catch (error) {
    console.error("Chat API error:", error);
    return new Response(JSON.stringify({ error: "Failed to process request" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
