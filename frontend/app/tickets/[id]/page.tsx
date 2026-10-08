"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  api,
  currentUser,
  type TicketDetail,
  type User
} from "@/lib/api";

const duration = (value: number | undefined) =>
  value === undefined ? "Not recorded" : `${Math.round(value)} ms`;

export default function TicketPage() {
  const id = useParams<{ id: string }>().id;
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setTicket(await api<TicketDetail>(`/api/v1/tickets/${id}`));
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load ticket.");
    }
  }

  useEffect(() => {
    setUser(currentUser());
    void load();
  }, [id]);

  async function act(path: string, body?: object) {
    setError("");
    setBusy(true);
    try {
      await api(`/api/v1/tickets/${id}/${path}`, {
        method: "POST",
        ...(body ? { body: JSON.stringify(body) } : {})
      });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Ticket action failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return <p className="surface p-8 text-center">Sign in with a support-agent account to view this case.</p>;
  }
  if (!ticket) {
    return (
      <div>
        {error && <p role="alert" className="mb-4 text-red-700">{error}</p>}
        <Link href="/tickets" className="text-[#087f5b]">← Back to queue</Link>
      </div>
    );
  }

  const run = ticket.agent_run;
  const stageTimings = run?.processing_metadata.stage_timings_ms ?? {};
  const closed = ticket.status === "resolved" || ticket.status === "closed";

  return (
    <div>
      <Link href="/tickets" className="text-sm font-semibold text-[#087f5b]">← Support queue</Link>
      <div className="mt-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-[#087f5b]">HUMAN REVIEW</p>
          <h1 className="mt-2 text-3xl font-semibold">
            Ticket <span className="font-mono text-xl text-[#65736f]">#{ticket.id.slice(0, 8)}</span>
          </h1>
          <p className="mt-3 max-w-2xl leading-6 text-[#65736f]">{ticket.reason}</p>
        </div>
        <div className="flex gap-2">
          {!closed && <button className="button-secondary" disabled={busy} onClick={() => act("assign", { assigned_to: user.id })}>Assign to me</button>}
          {!closed && ticket.status === "assigned" && <button className="button-secondary" disabled={busy} onClick={() => act("start")}>Start work</button>}
          {!closed && <button className="button-primary" disabled={busy} onClick={() => act("resolve", { resolution_metadata: { resolved_by: user.id } })}>Resolve</button>}
        </div>
      </div>
      {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}

      <div className="mt-7 grid gap-6 lg:grid-cols-[1.2fr_.8fr]">
        <section className="surface space-y-4 p-5">
          <h2 className="font-semibold">Conversation timeline</h2>
          {ticket.messages.map(message => (
            <div key={message.id} className="rounded-xl bg-[#f6f8f5] p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-semibold uppercase text-[#65736f]">{message.sender_type}</p>
                <time className="text-xs text-[#65736f]" dateTime={message.created_at}>
                  {new Date(message.created_at).toLocaleString()}
                </time>
              </div>
              <p className="mt-2 whitespace-pre-wrap leading-6">{message.content}</p>
            </div>
          ))}
        </section>

        <aside className="space-y-5">
          <section className="surface p-5">
            <h2 className="font-semibold">Case overview</h2>
            <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div><dt className="text-[#65736f]">Status</dt><dd className="mt-1 font-semibold capitalize">{ticket.status.replaceAll("_", " ")}</dd></div>
              <div><dt className="text-[#65736f]">Priority</dt><dd className="mt-1 font-semibold capitalize">{ticket.priority}</dd></div>
              <div className="col-span-2"><dt className="text-[#65736f]">Detected intent</dt><dd className="mt-1 font-semibold">{run?.intent?.replaceAll("_", " ") ?? "Not identified"}</dd></div>
              {run?.intent_reason && <div className="col-span-2"><dt className="text-[#65736f]">Intent signal</dt><dd className="mt-1">{run.intent_reason}</dd></div>}
              <div className="col-span-2"><dt className="text-[#65736f]">Evidence sufficiency</dt><dd className="mt-1 font-semibold capitalize">{run?.evidence_status ?? "Not evaluated"}</dd></div>
              {run?.evidence_reason && <div className="col-span-2"><dt className="text-[#65736f]">Evidence assessment</dt><dd className="mt-1">{run.evidence_reason}</dd></div>}
            </dl>
          </section>

          <section className="surface border-l-4 border-l-amber-500 p-5">
            <h2 className="font-semibold">Why Assistly escalated</h2>
            <p className="mt-2 text-sm leading-6 text-[#52625d]">{run?.escalation_reason ?? ticket.reason}</p>
            {run?.grounding && (
              <div className="mt-4 border-t border-[#e4eae6] pt-4 text-sm">
                <p className="font-medium">Grounding check: {run.grounding.supported ? "supported" : "not supported"}</p>
                <p className="mt-1 text-[#65736f]">{run.grounding.reason}</p>
              </div>
            )}
            {run?.error_category && <p className="mt-3 text-sm text-[#65736f]">Processing category: {run.error_category.replaceAll("_", " ")}</p>}
          </section>

          {run && (
            <section className="surface p-5">
              <h2 className="font-semibold">Run diagnostics</h2>
              <dl className="mt-4 space-y-3 text-sm">
                <div><dt className="text-[#65736f]">Request ID</dt><dd className="mt-1 break-all font-mono text-xs">{run.request_id}</dd></div>
                <div><dt className="text-[#65736f]">Provider / model</dt><dd className="mt-1">{run.provider ?? "Not recorded"} / {run.model ?? "Not recorded"}</dd></div>
                <div><dt className="text-[#65736f]">Total processing</dt><dd className="mt-1">{duration(run.latency_ms)}</dd></div>
                <div><dt className="text-[#65736f]">Retrieval / generation</dt><dd className="mt-1">{duration(stageTimings.retrieval_latency_ms)} / {duration(stageTimings.generation_latency_ms)}</dd></div>
                <div><dt className="text-[#65736f]">Intent confidence</dt><dd className="mt-1">{run.intent_confidence === null ? "Not calibrated" : `${(run.intent_confidence * 100).toFixed(1)}%`}</dd></div>
              </dl>
            </section>
          )}

          {run?.draft_reply && (
            <section className="surface p-5">
              <h2 className="font-semibold">AI draft <span className="text-xs font-normal text-[#65736f]">— internal review only</span></h2>
              <p className="mt-3 leading-6 text-[#52625d]">{run.draft_reply}</p>
            </section>
          )}

          {run?.evidence.length ? (
            <section className="surface p-5">
              <h2 className="font-semibold">Retrieved historical evidence</h2>
              {run.evidence.map((item, index) => (
                <div key={`${item.source_id}-${index}`} className="mt-4 border-t border-[#e4eae6] pt-4 text-sm">
                  <p className="text-[#65736f]">Evidence {index + 1} · {Math.round(item.retrieval_score * 100)}% retrieval score</p>
                  <p className="mt-2">{item.customer_message}</p>
                  <p className="mt-2 font-medium text-[#087f5b]">{item.support_response}</p>
                </div>
              ))}
            </section>
          ) : null}

          {ticket.resolution_metadata && (
            <section className="surface p-5">
              <h2 className="font-semibold">Resolution record</h2>
              <pre className="mt-3 overflow-auto whitespace-pre-wrap text-sm">{JSON.stringify(ticket.resolution_metadata, null, 2)}</pre>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}
