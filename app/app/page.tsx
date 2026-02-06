import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Database,
  Layers,
  Zap,
  Search,
  GitBranch,
  MessageSquare,
  ArrowRight,
  Check,
} from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Layers className="h-4 w-4" />
            </div>
            <span className="text-xl font-semibold">Contaixt</span>
          </div>
          <div className="flex items-center gap-4">
            <Button asChild variant="ghost">
              <Link href="/auth/login">Sign in</Link>
            </Button>
            <Button asChild>
              <Link href="/auth/sign-up">Get started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="border-b py-24">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl">
            The Context Layer
            <br />
            <span className="text-muted-foreground">for Your AI</span>
          </h1>
          <p className="mx-auto mb-10 max-w-2xl text-xl text-muted-foreground">
            Connect your data sources, build a unified knowledge graph, and give
            every AI application the context it needs. One vault, infinite
            possibilities.
          </p>
          <div className="flex justify-center gap-4">
            <Button asChild size="lg">
              <Link href="/auth/sign-up">
                Start building <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="#how-it-works">See how it works</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="border-b py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="mb-4 text-3xl font-bold">The Problem</h2>
            <p className="text-lg text-muted-foreground">
              Your company data lives in silos: Gmail, Notion, Google Drive,
              Slack. Every AI tool you build needs context, but fetching and
              structuring that data is a nightmare. You end up building the same
              RAG pipeline over and over.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="border-b py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="mb-4 text-center text-3xl font-bold">How It Works</h2>
          <p className="mx-auto mb-16 max-w-2xl text-center text-muted-foreground">
            Three steps to give your AI applications complete company context.
          </p>

          <div className="grid gap-8 md:grid-cols-3">
            {/* Step 1 */}
            <Card className="relative p-8">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Database className="h-6 w-6" />
              </div>
              <div className="mb-2 text-sm font-medium text-muted-foreground">
                Step 1
              </div>
              <h3 className="mb-3 text-xl font-semibold">
                Create a Context Vault
              </h3>
              <p className="text-muted-foreground">
                Define the scope of your knowledge base. Create vaults for
                different teams, projects, or use cases. Each vault is an
                isolated partition of your data.
              </p>
            </Card>

            {/* Step 2 */}
            <Card className="relative p-8">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Zap className="h-6 w-6" />
              </div>
              <div className="mb-2 text-sm font-medium text-muted-foreground">
                Step 2
              </div>
              <h3 className="mb-3 text-xl font-semibold">
                Connect Data Sources
              </h3>
              <p className="text-muted-foreground">
                One-click integrations with Gmail, Google Drive, Notion, Slack,
                and more. Data syncs continuously via webhooks. Always fresh,
                always up-to-date.
              </p>
            </Card>

            {/* Step 3 */}
            <Card className="relative p-8">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                <MessageSquare className="h-6 w-6" />
              </div>
              <div className="mb-2 text-sm font-medium text-muted-foreground">
                Step 3
              </div>
              <h3 className="mb-3 text-xl font-semibold">Query with Context</h3>
              <p className="text-muted-foreground">
                Ask questions, build chatbots, power agents. Every AI
                application retrieves the right context through a single API.
                Built-in citations and source tracking.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="border-b py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="mb-4 text-center text-3xl font-bold">
            Built for Scale
          </h2>
          <p className="mx-auto mb-16 max-w-2xl text-center text-muted-foreground">
            Enterprise-grade infrastructure for your knowledge layer.
          </p>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                <GitBranch className="h-5 w-5" />
              </div>
              <div>
                <h3 className="mb-1 font-semibold">Knowledge Graph</h3>
                <p className="text-sm text-muted-foreground">
                  Entities and relationships extracted automatically. Query
                  connections, not just documents.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Search className="h-5 w-5" />
              </div>
              <div>
                <h3 className="mb-1 font-semibold">Hybrid Search</h3>
                <p className="text-sm text-muted-foreground">
                  Vector embeddings + graph traversal. Find relevant context
                  even when keywords don't match.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <h3 className="mb-1 font-semibold">Context Vaults</h3>
                <p className="text-sm text-muted-foreground">
                  Partition data by team, project, or use case. Control exactly
                  which context flows where.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Zap className="h-5 w-5" />
              </div>
              <div>
                <h3 className="mb-1 font-semibold">Real-time Sync</h3>
                <p className="text-sm text-muted-foreground">
                  Webhook-driven updates. Changes in your data sources are
                  reflected within minutes.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Check className="h-5 w-5" />
              </div>
              <div>
                <h3 className="mb-1 font-semibold">Citations</h3>
                <p className="text-sm text-muted-foreground">
                  Every answer includes source links. Know exactly where
                  information comes from.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h3 className="mb-1 font-semibold">Single API</h3>
                <p className="text-sm text-muted-foreground">
                  One endpoint for all your context needs. Replace dozens of
                  custom integrations.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="border-b py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="mb-4 text-center text-3xl font-bold">Use Cases</h2>
          <p className="mx-auto mb-16 max-w-2xl text-center text-muted-foreground">
            One context layer, infinite applications.
          </p>

          <div className="grid gap-8 md:grid-cols-2">
            <Card className="p-6">
              <h3 className="mb-2 text-lg font-semibold">Internal Chatbots</h3>
              <p className="text-muted-foreground">
                Build AI assistants that actually know your company. Answer
                questions about projects, processes, and people with full
                context.
              </p>
            </Card>

            <Card className="p-6">
              <h3 className="mb-2 text-lg font-semibold">Sales Intelligence</h3>
              <p className="text-muted-foreground">
                Give your sales team instant access to customer history, past
                conversations, and relevant documents before every call.
              </p>
            </Card>

            <Card className="p-6">
              <h3 className="mb-2 text-lg font-semibold">Support Automation</h3>
              <p className="text-muted-foreground">
                Power support agents with product documentation, past tickets,
                and customer context. Faster resolution, happier customers.
              </p>
            </Card>

            <Card className="p-6">
              <h3 className="mb-2 text-lg font-semibold">Knowledge Search</h3>
              <p className="text-muted-foreground">
                Replace keyword search with semantic understanding. Find
                information across all your tools in one place.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h2 className="mb-4 text-3xl font-bold">
            Ready to build your context layer?
          </h2>
          <p className="mx-auto mb-8 max-w-xl text-muted-foreground">
            Stop rebuilding RAG pipelines. Start shipping AI features.
          </p>
          <Button asChild size="lg">
            <Link href="/auth/sign-up">
              Get started for free <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground">
                <Layers className="h-3 w-3" />
              </div>
              <span className="text-sm font-medium">Contaixt</span>
            </div>
            <p className="text-sm text-muted-foreground">
              The context layer for AI.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
