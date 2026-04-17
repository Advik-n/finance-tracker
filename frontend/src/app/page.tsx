import Link from "next/link";
import { ArrowRight, BarChart3, Shield, Sparkles, Upload } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" />
            <span className="text-xl font-semibold">FinSight AI</span>
          </div>
          <nav className="flex items-center gap-4">
            <Link
              href="/auth/login"
              className="text-sm font-medium text-muted-foreground hover:text-primary"
            >
              Login
            </Link>
            <Link
              href="/auth/register"
              className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
            >
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="container py-24 md:py-32">
          <div className="mx-auto flex max-w-[64rem] flex-col items-center gap-4 text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
              Your <span className="text-primary">Financial Intelligence</span>{" "}
              Layer
            </h1>
            <p className="max-w-[42rem] leading-normal text-muted-foreground sm:text-xl sm:leading-8">
              Upload statements, auto-categorize spend, and get CA-level
              insights across petrol, food, utilities, clothes, and groceries.
            </p>
            <div className="flex gap-4">
              <Link
                href="/auth/register"
                className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
              >
                Start Free Trial
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="#features"
                className="inline-flex h-11 items-center justify-center rounded-md border border-input bg-background px-8 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                Learn More
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="container py-24 md:py-32">
          <div className="mx-auto flex max-w-[58rem] flex-col items-center gap-4 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Powerful Features
            </h2>
            <p className="max-w-[42rem] text-muted-foreground sm:text-lg">
              Everything you need to manage your personal finances effectively.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-5xl gap-8 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<Upload className="h-8 w-8" />}
              title="Smart Statement Upload"
              description="Import PDF, CSV, or Excel statements with automated extraction and classification."
            />
            <FeatureCard
              icon={<Sparkles className="h-8 w-8" />}
              title="High-Accuracy Categorization"
              description="RAG-enhanced models prevent petrol and food misclassification."
            />
            <FeatureCard
              icon={<BarChart3 className="h-8 w-8" />}
              title="Professional Analytics"
              description="Interactive charts, aggregates, and benchmarked insights."
            />
            <FeatureCard
              icon={<Shield className="h-8 w-8" />}
              title="Privacy-First"
              description="Read-only analysis with encrypted sensitive fields."
            />
            <FeatureCard
              icon={<Sparkles className="h-8 w-8" />}
              title="Actionable Insights"
              description="Identify overspending and get targeted saving suggestions."
            />
            <FeatureCard
              icon={<BarChart3 className="h-8 w-8" />}
              title="Spending Focus"
              description="Instant totals for petrol, groceries, utilities, and clothing."
            />
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-6 md:py-0">
        <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
          <p className="text-sm text-muted-foreground">
            © 2024 AI Finance Tracker. All rights reserved.
          </p>
          <nav className="flex gap-4 text-sm text-muted-foreground">
            <Link href="/privacy" className="hover:text-primary">
              Privacy
            </Link>
            <Link href="/terms" className="hover:text-primary">
              Terms
            </Link>
            <Link href="/contact" className="hover:text-primary">
              Contact
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="group relative rounded-lg border bg-card p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="mb-4 text-primary">{icon}</div>
      <h3 className="mb-2 font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
