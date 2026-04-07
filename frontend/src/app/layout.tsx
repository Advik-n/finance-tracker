import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: {
    default: "AI Finance Tracker",
    template: "%s | AI Finance Tracker",
  },
  description: "AI-powered personal finance tracking and analytics platform",
  keywords: ["finance", "budget", "expense tracking", "AI", "analytics"],
  authors: [{ name: "Finance Tracker Team" }],
  creator: "Finance Tracker",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://financetracker.com",
    title: "AI Finance Tracker",
    description: "AI-powered personal finance tracking and analytics platform",
    siteName: "AI Finance Tracker",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Finance Tracker",
    description: "AI-powered personal finance tracking and analytics platform",
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
