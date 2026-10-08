"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, currentUser, type Conversation, type User } from "@/lib/api";

export default function DashboardPage() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setItems(await api<Conversation[]>("/api/v1/conversations"));
      setError("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load conversations."); }
  }
  useEffect(() => { setUser(currentUser()); void load(); }, []);

  async function createConversation() {
    setBusy(true);
    try {
      const conversation = await api<Conversation>("/api/v1/conversations", { method: "POST", body: JSON.stringify({ metadata: {} }) });
      window.location.href = `/conversations/${conversation.id}`;
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create a conversation."); }
    finally { setBusy(false); }
  }

  if (!user) return <SignInNotice />;
  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-sm font-semibold text-[#087f5b]">WORKSPACE</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Conversations</h1><p className="mt-2 text-[#65736f]">A clear view of customer requests and their next step.</p></div>
        {user.role === "customer" && <button className="button-primary" onClick={createConversation} disabled={busy}>{busy ? "Creating…" : "＋ New conversation"}</button>}
      </div>
      {error && <p role="alert" className="mt-6 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}
      <div className="surface mt-8 overflow-hidden">
        {items.length ? items.map(item => <Link key={item.id} href={`/conversations/${item.id}`} className="flex items-center justify-between border-b border-[#e4eae6] px-5 py-5 last:border-0 hover:bg-[#fbfcfb]">
          <div><p className="font-semibold">Conversation <span className="font-mono text-xs text-[#65736f]">#{item.id.slice(0, 8)}</span></p><p className="mt-1 text-sm text-[#65736f]">Updated {new Date(item.updated_at).toLocaleString()}</p></div>
          <Status value={item.status} />
        </Link>) : <div className="px-6 py-16 text-center"><div className="mx-auto grid size-12 place-items-center rounded-2xl bg-[#eaf5ef] text-xl text-[#087f5b]">↗</div><h2 className="mt-4 font-semibold">No conversations yet</h2><p className="mt-2 text-sm text-[#65736f]">{user.role === "customer" ? "Start a conversation and we’ll help you find the right next step." : "No customer conversations are assigned to your queue."}</p></div>}
      </div>
    </div>
  );
}

function Status({ value }: { value: string }) {
  return <span className="rounded-full bg-[#edf3ef] px-3 py-1 text-xs font-semibold capitalize text-[#52625d]">{value.replaceAll("_", " ")}</span>;
}

function SignInNotice() {
  return <div className="surface mx-auto mt-14 max-w-lg p-8 text-center"><h1 className="text-2xl font-semibold">Sign in to your workspace</h1><p className="mt-2 text-[#65736f]">Your conversations are available after authentication.</p><Link className="button-primary mt-5 inline-block" href="/login">Continue to sign in</Link></div>;
}
