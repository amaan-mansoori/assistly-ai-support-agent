"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, currentUser, type Ticket, type User } from "@/lib/api";

export default function TicketsPage() {
  const [items, setItems] = useState<Ticket[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setUser(currentUser());
    api<Ticket[]>("/api/v1/tickets").then(setItems).catch(reason => setError(reason instanceof Error ? reason.message : "Could not load tickets."));
  }, []);
  if (!user) return <p className="surface p-8 text-center">Sign in with a support-agent account to access the review queue.</p>;
  return <div><p className="text-sm font-semibold text-[#087f5b]">HUMAN REVIEW</p><h1 className="mt-2 text-3xl font-semibold">Support queue</h1><p className="mt-2 text-[#65736f]">Escalated cases that need a human decision.</p>{error && <p role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}
    <div className="surface mt-7 overflow-hidden">{items.length ? items.map(ticket => <Link href={`/tickets/${ticket.id}`} key={ticket.id} className="grid gap-3 border-b border-[#e4eae6] px-5 py-5 last:border-0 hover:bg-[#fbfcfb] sm:grid-cols-[1fr_auto]"><div><div className="flex flex-wrap items-center gap-2"><span className="font-semibold">Case <span className="font-mono text-xs text-[#65736f]">#{ticket.id.slice(0, 8)}</span></span><span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${ticket.priority === "urgent" || ticket.priority === "high" ? "bg-red-50 text-red-700" : "bg-[#edf3ef] text-[#52625d]"}`}>{ticket.priority}</span></div><p className="mt-2 text-sm text-[#65736f]">{ticket.reason}</p></div><span className="self-center text-xs font-semibold capitalize text-[#52625d]">{ticket.status.replaceAll("_", " ")}</span></Link>) : <div className="p-14 text-center"><h2 className="font-semibold">Queue is clear</h2><p className="mt-2 text-sm text-[#65736f]">There are no tickets available for your account.</p></div>}</div>
  </div>;
}
