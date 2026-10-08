"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { clearSession, currentUser, type User } from "@/lib/api";

export function AppNav() {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    const update = () => setUser(currentUser());
    update();
    window.addEventListener("support-session-change", update);
    return () => window.removeEventListener("support-session-change", update);
  }, []);
  if (!user) return <Link className="text-sm font-semibold text-[#087f5b]" href="/login">Sign in</Link>;
  return (
    <nav className="flex items-center gap-5 text-sm">
      <Link href="/dashboard" className="text-[#52625d] hover:text-[#087f5b]">Conversations</Link>
      {(user.role === "agent" || user.role === "admin") && <Link href="/tickets" className="text-[#52625d] hover:text-[#087f5b]">Review queue</Link>}
      {user.role === "admin" && <Link href="/analytics" className="text-[#52625d] hover:text-[#087f5b]">Analytics</Link>}
      <span className="hidden text-[#65736f] sm:inline">{user.email ?? user.role}</span>
      <button className="button-secondary !px-3 !py-2" onClick={() => { clearSession(); window.location.href = "/login"; }}>Sign out</button>
    </nav>
  );
}
