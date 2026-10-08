"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type AgentRun, type Conversation, type Message, type Submission } from "@/lib/api";

export default function ConversationPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [lastRun, setLastRun] = useState<AgentRun | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const [detail, history] = await Promise.all([
        api<Conversation>(`/api/v1/conversations/${id}`),
        api<Message[]>(`/api/v1/conversations/${id}/messages`)
      ]);
      setConversation(detail);
      setMessages(history);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load conversation."); }
  }
  useEffect(() => { void load(); }, [id]);

  async function send(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.trim()) return;
    setBusy(true); setError("");
    try {
      const result = await api<Submission>(`/api/v1/conversations/${id}/messages`, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ content: draft })
      });
      setDraft("");
      setLastRun(result.agent_run);
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Message could not be sent."); }
    finally { setBusy(false); }
  }

  async function rate(rating: number) {
    if (!lastRun) return;
    try {
      await api("/api/v1/feedback", { method: "POST", body: JSON.stringify({ conversation_id: id, agent_run_id: lastRun.id, rating }) });
      setError("Thanks for your feedback.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Feedback could not be saved."); }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/dashboard" className="text-sm font-semibold text-[#087f5b]">← All conversations</Link>
      <div className="mt-5 flex items-center justify-between"><div><p className="text-sm text-[#65736f]">CUSTOMER SUPPORT</p><h1 className="mt-1 text-2xl font-semibold">Conversation <span className="font-mono text-base text-[#65736f]">#{id.slice(0, 8)}</span></h1></div>{conversation && <span className="rounded-full bg-[#edf3ef] px-3 py-1 text-xs font-semibold capitalize">{conversation.status.replaceAll("_", " ")}</span>}</div>
      <section className="surface mt-6 min-h-[420px] space-y-5 p-5 sm:p-8">
        {messages.map(message => <div key={message.id} className={`flex ${message.sender_type === "customer" ? "justify-end" : "justify-start"}`}><div className={`max-w-[85%] rounded-2xl px-4 py-3 ${message.sender_type === "customer" ? "bg-[#087f5b] text-white" : "bg-[#f1f5f2]"}`}><p className="mb-1 text-xs font-semibold opacity-70">{message.sender_type === "customer" ? "You" : message.sender_type === "assistant" ? "Assistly" : "Support"}</p><p className="whitespace-pre-wrap leading-6">{message.content}</p></div></div>)}
        {!messages.length && <div className="grid min-h-[350px] place-items-center text-center"><div><div className="mx-auto grid size-12 place-items-center rounded-2xl bg-[#eaf5ef] text-xl text-[#087f5b]">✳</div><h2 className="mt-4 font-semibold">How can we help?</h2><p className="mt-2 text-sm text-[#65736f]">Describe what happened. If the answer isn’t clear, we’ll route it to a person.</p></div></div>}
      </section>
      {lastRun && <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-[#e4eae6] bg-white px-4 py-3 text-sm"><span className="text-[#65736f]">Was this helpful?</span>{[1, 2, 3, 4, 5].map(score => <button key={score} className="rounded-lg px-2 py-1 font-semibold text-[#087f5b] hover:bg-[#eaf5ef]" onClick={() => rate(score)} aria-label={`Rate ${score} out of 5`}>{score}</button>)}{lastRun.decision === "escalate" && <span className="ml-auto font-semibold text-amber-700">A support specialist will follow up.</span>}</div>}
      {error && <p role="status" className="mt-3 text-sm text-[#65736f]">{error}</p>}
      <form onSubmit={send} className="surface mt-4 flex items-end gap-3 p-3"><textarea className="field min-h-14 resize-y border-0 shadow-none focus:shadow-none" rows={2} maxLength={10000} placeholder="Write your message…" value={draft} onChange={e => setDraft(e.target.value)} /><button className="button-primary mb-1" disabled={busy || !draft.trim()}>{busy ? "Sending…" : "Send"}</button></form>
    </div>
  );
}
