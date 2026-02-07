"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useRef, useEffect, useState, useMemo } from "react";
import { Send, ExternalLink, Loader2, StopCircle, MessageSquare, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import ReactMarkdown from "react-markdown";

export default function OverviewPage() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [input, setInput] = useState("");

  const transport = useMemo(
    () => new DefaultChatTransport({ api: "/api/chat" }),
    []
  );

  const { messages, sendMessage, status, stop } = useChat({
    transport,
  });

  const isLoading = status === "submitted" || status === "streaming";

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input?.trim() || isLoading) return;

    const message = input.trim();
    setInput("");
    await sendMessage({ text: message });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  const handleSuggestionClick = async (suggestion: string) => {
    if (isLoading) return;
    setInput("");
    await sendMessage({ text: suggestion });
  };

  // Extract text content from message parts
  const getMessageContent = (message: typeof messages[0]): string => {
    // AI SDK v5+ uses parts array
    if (message.parts) {
      return message.parts
        .filter((part): part is { type: "text"; text: string } => part.type === "text")
        .map((part) => part.text)
        .join("");
    }
    return "";
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Overview</h1>
      </div>

      {/* Chat Messages */}
      <Card className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center max-w-md">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                  <MessageSquare className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-xl font-semibold">Welcome to Contaixt</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Start by asking a question about your connected data sources.
                </p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  <Badge variant="secondary">GraphRAG</Badge>
                  <Badge variant="secondary">Knowledge Graph</Badge>
                  <Badge variant="secondary">AI-Powered</Badge>
                </div>
                <div className="mt-6 space-y-3">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Try asking</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {[
                      "What do you know about me?",
                      "Summarize my recent emails",
                      "What projects am I working on?",
                    ].map((suggestion) => (
                      <Button
                        key={suggestion}
                        variant="outline"
                        size="sm"
                        className="rounded-full text-xs"
                        onClick={() => handleSuggestionClick(suggestion)}
                        disabled={isLoading}
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {message.role === "assistant" && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        <Sparkles className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    {message.role === "user" ? (
                      <p className="whitespace-pre-wrap">{getMessageContent(message)}</p>
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown
                          components={{
                            a: ({ href, children }) => (
                              <a
                                href={href}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-blue-600 hover:underline dark:text-blue-400"
                              >
                                {children}
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            ),
                          }}
                        >
                          {getMessageContent(message)}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      <Sparkles className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="space-y-2 rounded-lg bg-muted px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-[250px]" />
                      <Skeleton className="h-4 w-[200px]" />
                    </div>
                  </div>
                </div>
              )}

              <div ref={scrollRef} />
            </div>
          )}
        </ScrollArea>
      </Card>

      {/* Input Area */}
      <form onSubmit={onSubmit} className="mt-4">
        <div className="relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your knowledge base..."
            className="min-h-[60px] max-h-[200px] resize-none pr-24"
            disabled={isLoading}
            rows={1}
          />
          <div className="absolute bottom-2 right-2 flex gap-2">
            {isLoading ? (
              <Button
                type="button"
                size="icon"
                variant="outline"
                onClick={() => stop()}
              >
                <StopCircle className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                type="submit"
                size="icon"
                disabled={!input?.trim()}
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}
