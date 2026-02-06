"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useRef, useEffect, useState, useMemo } from "react";
import { Send, ExternalLink, StopCircle, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
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
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
          <span className="rounded-full border border-[hsl(var(--brand-purple-1)/0.35)] bg-[hsl(var(--brand-purple-1)/0.12)] px-3 py-1 text-xs font-medium text-[hsl(var(--brand-purple-2))]">
            Knowledge Chat
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          Ask questions about your knowledge base
        </p>
      </div>

      {/* Chat Messages */}
      <Card className="relative flex-1 gap-0 overflow-hidden border-border/60 bg-card/60 p-0 shadow-[0_24px_60px_-48px_rgba(59,45,186,0.45)]">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(1200px_circle_at_20%_-20%,rgba(99,102,241,0.18),transparent_60%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(900px_circle_at_90%_120%,rgba(139,92,246,0.16),transparent_55%)]" />
        </div>
        <ScrollArea className="relative z-10 h-full px-6 py-6">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center px-6 text-muted-foreground">
              <div className="text-center">
                <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(140deg,hsl(var(--brand-purple-1)),hsl(var(--brand-purple-3)))] shadow-[0_18px_40px_-22px_hsl(var(--brand-purple-1)/0.45)]">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <p className="text-lg font-semibold text-foreground">
                  Welcome to <span className="text-gradient-purple">Contaixt</span>
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Start by asking a question about your connected data sources.
                </p>
                <div className="mt-6 space-y-2 text-sm">
                  <p className="text-muted-foreground">Try asking:</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {[
                      "What do you know about me?",
                      "Summarize my recent emails",
                      "What projects am I working on?",
                    ].map((suggestion, index) => (
                      <button
                        key={suggestion}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="animate-float rounded-full border border-border/60 bg-background/70 px-3 py-1 text-xs text-foreground shadow-sm shadow-transparent transition hover:border-[hsl(var(--brand-purple-1)/0.5)] hover:bg-[hsl(var(--brand-purple-1)/0.12)] hover:text-foreground hover:shadow-[0_12px_24px_-18px_rgba(88,70,200,0.6)] disabled:cursor-not-allowed disabled:opacity-60"
                        style={{ animationDelay: `${index * 0.2}s` }}
                        disabled={isLoading}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message) => {
                const isUser = message.role === "user";
                return (
                  <div
                    key={message.id}
                    className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm lg:max-w-[70%] ${
                        isUser
                          ? "bg-gradient-to-br from-[hsl(var(--brand-purple-1))] via-[#5a4adf] to-[hsl(var(--brand-purple-3))] text-white shadow-[0_18px_45px_rgba(91,63,215,0.25)] ring-1 ring-white/10"
                          : "border border-border/60 border-l-2 border-l-[hsl(var(--brand-purple-1))] bg-background/80 text-foreground shadow-[0_16px_40px_-28px_rgba(15,23,42,0.3)] backdrop-blur"
                      }`}
                    >
                      {isUser ? (
                        <p className="whitespace-pre-wrap">{getMessageContent(message)}</p>
                      ) : (
                        <div className="prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed">
                          <ReactMarkdown
                            components={{
                              a: ({ href, children }) => (
                                <a
                                  href={href}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-[hsl(var(--brand-purple-2))] hover:text-[hsl(var(--brand-purple-1))] hover:underline"
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
                );
              })}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-3 rounded-2xl border border-border/60 bg-background/80 px-4 py-3 text-sm shadow-sm backdrop-blur">
                    <div className="flex items-center gap-1">
                      <span className="h-2 w-2 rounded-full bg-muted-foreground/70 animate-typing" />
                      <span
                        className="h-2 w-2 rounded-full bg-muted-foreground/70 animate-typing"
                        style={{ animationDelay: "0.15s" }}
                      />
                      <span
                        className="h-2 w-2 rounded-full bg-muted-foreground/70 animate-typing"
                        style={{ animationDelay: "0.3s" }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">Thinking...</span>
                  </div>
                </div>
              )}

              <div ref={scrollRef} />
            </div>
          )}
        </ScrollArea>
      </Card>

      {/* Input Area */}
      <form onSubmit={onSubmit} className="mt-2">
        <div className="relative group">
          <div className="pointer-events-none absolute -inset-[1px] rounded-2xl bg-gradient-to-r from-[hsl(var(--brand-purple-1)/0.4)] via-transparent to-[hsl(var(--brand-purple-2)/0.4)] opacity-0 transition duration-300 group-focus-within:opacity-100" />
          <div className="relative rounded-2xl border border-border/60 bg-background/80 p-4 shadow-lg shadow-black/5 backdrop-blur">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your knowledge base..."
              className="min-h-[60px] max-h-[200px] resize-none border-0 bg-transparent p-0 pr-24 text-sm shadow-none focus-visible:border-transparent focus-visible:ring-0"
              disabled={isLoading}
              rows={1}
            />
            <div className="absolute bottom-3 right-3 flex gap-2">
              {isLoading ? (
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={() => stop()}
                  className="h-9 w-9 rounded-full border-border/60 bg-background/80 shadow-sm"
                >
                  <StopCircle className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  size="icon"
                  disabled={!input?.trim()}
                  className="h-9 w-9 rounded-full bg-gradient-to-br from-[hsl(var(--brand-purple-1))] to-[hsl(var(--brand-purple-3))] text-white shadow-[0_16px_30px_-18px_hsl(var(--brand-purple-1)/0.5)] transition hover:opacity-90 disabled:opacity-40"
                >
                  <Send className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}
