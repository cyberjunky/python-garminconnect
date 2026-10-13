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
    <div className="dash-nav-container">
      <nav className="dash-nav" aria-label="Navegación principal">
        <div className="dash-nav-scroll-area">
          <span className="dash-brand">Tri-Coach</span>
          <div className="dash-nav-links">
            {LINKS.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={path === href ? "dash-nav-link active" : "dash-nav-link"}
                aria-current={path === href ? "page" : undefined}
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
        <div className="dash-nav-pinned">
          <button
            type="button"
            className={`dash-refresh ${state === "loading" ? "is-loading" : ""}`}
            onClick={refreshStatus}
            disabled={state === "loading"}
            aria-label="Actualizar datos de Garmin"
            aria-busy={state === "loading"}
            title="Actualizar datos de Garmin"
          >
            <span className="dash-refresh-icon" aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                width="16"
                height="16"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                <path d="M16 21h5v-5" />
              </svg>
            </span>
            <span className="dash-refresh-label">
              {state === "loading" ? "Actualizando…" : "Actualizar"}
            </span>
          </button>
        </div>
      </nav>
      {message ? (
        <div
          className={`dash-refresh-banner ${state === "error" ? "error" : "ok"}`}
          role={state === "error" ? "alert" : "status"}
          aria-live="polite"
        >
          {message}
        </div>
      ) : null}
      <p className="dash-version">{version}</p>
    </div>
  );
}
