"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useTransition } from "react";
import { ClientAuthService } from "@/lib/infra/auth/clientAuthService";

export const dynamic = "force-dynamic";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get("next") || "/";

  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [step, setStep] = useState<"email" | "otp">("email");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const authService = new ClientAuthService();

  useEffect(() => {
    void authService.getSession().then((session) => {
      if (session?.user) {
        router.replace(nextUrl);
      }
    });
  }, [nextUrl, router]);

  async function handleRequestOtp(e: React.FormEvent) {
    e.preventDefault();
    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setErrorMessage("Por favor ingresa tu correo electrónico registrado.");
      return;
    }

    setErrorMessage(null);
    setStatusMessage(null);

    startTransition(async () => {
      const result = await authService.requestEmailOtp(cleanEmail);
      if (!result.ok) {
        setErrorMessage(
          result.error || "No se pudo enviar el código. Verifica que tu cuenta haya sido invitada."
        );
        return;
      }

      setStep("otp");
      setStatusMessage(`Hemos enviado un código OTP de 6 dígitos a ${cleanEmail}.`);
    });
  }

  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    const cleanToken = token.trim();
    if (!cleanToken) {
      setErrorMessage("Por favor ingresa el código recibido.");
      return;
    }

    setErrorMessage(null);

    startTransition(async () => {
      const result = await authService.verifyEmailOtp(email, cleanToken);
      if (!result.ok || !result.session) {
        setErrorMessage(result.error || "Código incorrecto o expirado. Intenta nuevamente.");
        return;
      }

      setStatusMessage("Sesión iniciada correctamente. Redirigiendo…");
      router.replace(nextUrl);
    });
  }

  return (
    <div className="login-card">
      <div className="login-header">
        <Link href="/" className="login-back" aria-label="Volver al inicio">
          ← Inicio
        </Link>
        <h1 className="login-title">Iniciar sesión</h1>
        <p className="login-subtitle muted">
          Acceso privado por invitación a tu entrenador Tri-Coach
        </p>
      </div>

      {errorMessage ? (
        <div className="dash-refresh-status error login-alert" role="alert">
          {errorMessage}
        </div>
      ) : null}

      {statusMessage ? (
        <div className="dash-refresh-banner login-alert" role="status">
          {statusMessage}
        </div>
      ) : null}

      {step === "email" ? (
        <form onSubmit={handleRequestOtp} className="login-form">
          <label htmlFor="login-email" className="login-label">
            Correo electrónico
          </label>
          <input
            id="login-email"
            type="email"
            className="login-input"
            placeholder="atleta@garmin.co"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isPending}
            required
            autoFocus
            autoComplete="email"
          />
          <button
            type="submit"
            className="coach-send login-submit"
            disabled={isPending || !email.trim()}
          >
            {isPending ? "Enviando código…" : "Continuar con código OTP"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOtp} className="login-form">
          <label htmlFor="login-otp" className="login-label">
            Código de verificación (6 dígitos)
          </label>
          <input
            id="login-otp"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            className="login-input login-input-otp"
            placeholder="123456"
            maxLength={8}
            value={token}
            onChange={(e) => setToken(e.target.value)}
            disabled={isPending}
            required
            autoFocus
            autoComplete="one-time-code"
          />
          <button
            type="submit"
            className="coach-send login-submit"
            disabled={isPending || !token.trim()}
          >
            {isPending ? "Verificando…" : "Ingresar a Tri-Coach"}
          </button>
          <button
            type="button"
            className="coach-history-item login-resend"
            onClick={() => {
              setStep("email");
              setToken("");
              setErrorMessage(null);
              setStatusMessage(null);
            }}
            disabled={isPending}
          >
            Cambiar correo o reenviar código
          </button>
        </form>
      )}
    </div>
  );
}

export default function LoginPage() {
  return (
    <main className="login-main">
      <Suspense fallback={<div className="login-card"><p className="muted">Cargando…</p></div>}>
        <LoginForm />
      </Suspense>
    </main>
  );
}
