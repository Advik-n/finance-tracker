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
            <span className="text-xl font-bold">AI Finance Tracker</span>
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
              Take Control of Your{" "}
              <span className="text-primary">Finances</span> with AI
            </h1>
            <p className="max-w-[42rem] leading-normal text-muted-foreground sm:text-xl sm:leading-8">
              Upload bank statements, auto-categorize transactions, and get
              AI-powered insights to optimize your spending and savings.
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
              title="Smart Upload"
              description="Upload PDF, CSV, or Excel bank statements. Our AI automatically extracts and categorizes transactions."
            />
            <FeatureCard
              icon={<Sparkles className="h-8 w-8" />}
              title="AI Categorization"
              description="Transactions are automatically categorized using machine learning, saving you hours of manual work."
            />
            <FeatureCard
              icon={<BarChart3 className="h-8 w-8" />}
              title="Visual Analytics"
              description="Beautiful charts and insights show exactly where your money goes each month."
            />
            <FeatureCard
              icon={<Shield className="h-8 w-8" />}
              title="Bank-Level Security"
              description="Your financial data is encrypted and protected with enterprise-grade security measures."
            />
            <FeatureCard
              icon={<Sparkles className="h-8 w-8" />}
              title="Smart Insights"
              description="Get personalized recommendations to reduce spending and increase savings."
            />
            <FeatureCard
              icon={<BarChart3 className="h-8 w-8" />}
              title="Budget Tracking"
              description="Set budgets by category and get alerts when you're close to your limits."
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
