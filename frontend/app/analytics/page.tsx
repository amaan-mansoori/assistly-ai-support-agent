"use client";

import { useEffect, useState } from "react";
import { api, currentUser, type User } from "@/lib/api";

type Analytics = { total_conversations: number; auto_handle_rate: number | null; escalation_rate: number | null; resolution_rate: number | null; average_latency_ms: number | null; average_feedback_rating: number | null; intent_distribution: Record<string, number>; error_categories: Record<string, number> };
const percent = (value: number | null) => value === null ? "—" : `${(value * 100).toFixed(1)}%`;

export default function AnalyticsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setUser(currentUser());
    api<Analytics>("/api/v1/analytics").then(setData).catch(reason => setError(reason instanceof Error ? reason.message : "Could not load analytics."));
  }, []);
  if (!user || user.role !== "admin") return <div className="surface mx-auto max-w-lg p-8 text-center"><h1 className="text-xl font-semibold">Admin access required</h1><p className="mt-2 text-sm text-[#65736f]">Analytics are visible to administrators only.</p></div>;
  if (error) return <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-700">{error}</p>;
  if (!data) return <p className="text-[#65736f]">Loading analytics…</p>;
  const cards = [["Conversations", data.total_conversations.toLocaleString()], ["Auto-handle", percent(data.auto_handle_rate)], ["Escalated", percent(data.escalation_rate)], ["Ticket resolution", percent(data.resolution_rate)], ["Average latency", data.average_latency_ms === null ? "—" : `${Math.round(data.average_latency_ms)} ms`], ["Feedback score", data.average_feedback_rating === null ? "—" : `${data.average_feedback_rating.toFixed(1)} / 5`]];
  return <div><p className="text-sm font-semibold text-[#087f5b]">OPERATIONS</p><h1 className="mt-2 text-3xl font-semibold">Support analytics</h1><p className="mt-2 text-[#65736f]">Live aggregates from persisted platform data. Empty values mean no observations yet.</p><div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{cards.map(([label, value]) => <div className="surface p-5" key={label}><p className="text-sm text-[#65736f]">{label}</p><p className="mt-3 text-3xl font-semibold tracking-tight">{value}</p></div>)}</div><div className="mt-7 grid gap-5 lg:grid-cols-2"><Distribution title="Intent distribution" values={data.intent_distribution} /><Distribution title="Recorded failure categories" values={data.error_categories} /></div></div>;
}

function Distribution({ title, values }: { title: string; values: Record<string, number> }) {
  const rows = Object.entries(values).sort((a, b) => b[1] - a[1]);
  return <section className="surface p-5"><h2 className="font-semibold">{title}</h2>{rows.length ? <div className="mt-4 space-y-3">{rows.map(([name, count]) => <div key={name} className="flex items-center justify-between gap-4 text-sm"><span className="break-all text-[#52625d]">{name.replaceAll("_", " ")}</span><span className="font-semibold">{count}</span></div>)}</div> : <p className="mt-4 text-sm text-[#65736f]">No data available yet.</p>}</section>;
}
