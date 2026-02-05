import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Redirect logged-in users to the app
  if (user) {
    redirect("/overview");
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="text-center">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2L2 7L12 12L22 7L12 2Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M2 17L12 22L22 17"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M2 12L12 17L22 12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
        </div>

        <h1 className="mb-4 text-4xl font-bold tracking-tight">Contaixt</h1>
        <p className="mb-8 max-w-md text-lg text-muted-foreground">
          Connect your data sources and build a knowledge layer for AI-powered
          insights.
        </p>

        <div className="flex justify-center gap-4">
          <Button asChild size="lg" variant="outline">
            <Link href="/auth/login">Sign in</Link>
          </Button>
          <Button asChild size="lg">
            <Link href="/auth/sign-up">Get started</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
