"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, saveSession, type User } from "@/lib/api";

type AuthResult = { access_token: string; user: User };

export default function LoginPage() {
  const router = useRouter();
  const [register, setRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const result = await api<AuthResult>(`/api/v1/auth/${register ? "register" : "token"}`, {
        method: "POST", body: JSON.stringify({ email, password })
      });
      saveSession(result.access_token, result.user);
      router.push("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl items-center gap-12 py-12 md:grid-cols-[1.1fr_.9fr]">
      <section>
        <p className="mb-3 text-sm font-bold uppercase tracking-[.18em] text-[#087f5b]">Thoughtful support, in one place</p>
        <h1 className="max-w-xl text-5xl font-semibold leading-[1.08] tracking-[-.04em]">Every customer deserves a clear answer.</h1>
        <p className="mt-5 max-w-lg leading-7 text-[#65736f]">Bring AI-assisted conversations and human follow-up together. Uncertain requests are routed to the support team.</p>
      </section>
      <form onSubmit={submit} className="surface p-7 shadow-[0_12px_40px_#19392a0a]">
        <h2 className="text-xl font-semibold">{register ? "Create a customer account" : "Welcome back"}</h2>
        <p className="mt-1 text-sm text-[#65736f]">{register ? "Start a new support conversation." : "Sign in to continue to your workspace."}</p>
        <label className="mt-6 block text-sm font-semibold">Email<input className="field mt-2" type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></label>
        <label className="mt-4 block text-sm font-semibold">Password<input className="field mt-2" type="password" required minLength={register ? 12 : 1} autoComplete={register ? "new-password" : "current-password"} value={password} onChange={e => setPassword(e.target.value)} /></label>
        {error && <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <button className="button-primary mt-6 w-full" disabled={busy}>{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</button>
        <p className="mt-5 text-center text-sm text-[#65736f]">{register ? "Already have an account?" : "New to Assistly?"}{" "}
          <button className="font-semibold text-[#087f5b]" type="button" onClick={() => { setError(""); setRegister(!register); }}>{register ? "Sign in" : "Create account"}</button>
        </p>
        <p className="mt-5 border-t border-[#e4eae6] pt-4 text-xs leading-5 text-[#65736f]">New registrations are customer accounts. Support staff accounts must be provisioned by an administrator.</p>
        <Link className="sr-only" href="/dashboard">Continue to conversations</Link>
      </form>
    </div>
  );
}
