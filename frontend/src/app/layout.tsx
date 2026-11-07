import type { Metadata, Viewport } from "next";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "GTM Outreach: Personalized Outreach Intelligence",
  description: "AI-powered B2B research and personalized outreach drafting.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font -- Host Grotesk and
            Atkinson Hyperlegible Mono aren't in next/font/google's bundled list; a direct
            link in the root layout's head is Next's documented App Router pattern for
            external fonts it doesn't self-host. */}
        <link
          href="https://fonts.googleapis.com/css2?family=Host+Grotesk:wght@400;500&family=Atkinson+Hyperlegible+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-full min-h-screen bg-paper text-ink">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
