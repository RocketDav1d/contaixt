export default function Loading() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="text-center">
        <div className="mb-8 flex justify-center">
          <div className="flex h-16 w-16 animate-pulse items-center justify-center rounded-2xl bg-muted" />
        </div>
        <div className="h-10 w-48 animate-pulse rounded bg-muted mx-auto mb-4" />
        <div className="h-6 w-64 animate-pulse rounded bg-muted mx-auto" />
      </div>
    </main>
  );
}
