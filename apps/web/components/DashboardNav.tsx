"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

const LINKS = [
  { href: "/", label: "Hoy" },
  { href: "/retos", label: "Retos" },
  { href: "/mesociclos", label: "Mesociclos" },
  { href: "/70-3-cartagena", label: "70.3 Cartagena" },
];

type RefreshState = "idle" | "loading" | "ok" | "error";

type RefreshBody = {
  ok?: boolean;
  pending?: boolean;
  status?: string;
  conclusion?: string | null;
  error?: string;
  message?: string;
};

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function DashboardNav({ version }: { version: string }) {
  const path = usePathname();
  const router = useRouter();
  const [state, setState] = useState<RefreshState>("idle");
  const [message, setMessage] = useState<string | null>(null);

  async function refreshStatus() {
    setState("loading");
    setMessage("Consultando Garmin…");
    const started = new Date().toISOString();
    try {
      const res = await fetch("/api/refresh", { method: "POST" });
      const body = (await res.json()) as RefreshBody;
      if (!res.ok || !body.ok) {
        setState("error");
        setMessage(body.error || "No se pudo actualizar");
        return;
      }

      for (let attempt = 0; attempt < 36; attempt += 1) {
        await sleep(5000);
        const statusRes = await fetch(`/api/refresh?since=${encodeURIComponent(started)}`);
        const statusBody = (await statusRes.json()) as RefreshBody;
        if (!statusRes.ok || !statusBody.ok) {
          setState("error");
          setMessage(statusBody.error || "No se pudo leer el estado de GitHub");
          return;
        }
        if (statusBody.pending || statusBody.status !== "completed") {
          setMessage("Consultando Garmin en GitHub…");
          continue;
        }
        if (statusBody.conclusion === "success") {
          setState("ok");
          setMessage("Garmin actualizado");
          router.refresh();
          return;
        }
        setState("error");
        setMessage("La recolección en GitHub falló");
        return;
      }

      setState("error");
      setMessage("La recolección sigue en curso. Vuelve a abrir Hoy en un minuto.");
    } catch {
      setState("error");
      setMessage("No se pudo actualizar");
    }
  }

  return (
    <nav className="dash-nav" aria-label="Secciones">
      <p className="dash-brand">Fitness Coach</p>
      {LINKS.map(({ href, label }) => (
        <Link key={href} href={href} className={path === href ? "dash-nav-link active" : "dash-nav-link"}>
          {label}
        </Link>
      ))}
      <button type="button" className="dash-refresh" onClick={refreshStatus} disabled={state === "loading"}>
        {state === "loading" ? "Actualizando…" : "Actualizar"}
      </button>
      {message ? (
        <p className={state === "error" ? "dash-refresh-status error" : "dash-refresh-status"} role="status">
          {message}
        </p>
      ) : null}
      <p className="dash-version">{version}</p>
    </nav>
  );
}
