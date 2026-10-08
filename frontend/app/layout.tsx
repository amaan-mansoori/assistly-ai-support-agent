import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { AppNav } from "@/components/app-nav";

export const metadata: Metadata = {
  title: "Assistly | AI-Powered Customer Support Platform",
  description: "AI-powered customer support, grounded in real resolutions."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-[#e4eae6] bg-white">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <Link href="/dashboard" className="flex items-center gap-3 font-bold tracking-tight">
              <span className="grid size-9 place-items-center rounded-xl bg-[#087f5b] text-white">A</span>
              <span>Assistly <span className="font-normal text-[#65736f]">support</span></span>
            </Link>
            <AppNav />
          </div>
        </header>
        <main className="mx-auto min-h-[calc(100vh-74px)] max-w-7xl px-6 py-9">{children}</main>
      </body>
    </html>
  );
}
