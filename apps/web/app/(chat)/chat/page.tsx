import { CoachChatScreen } from "@/components/CoachChatScreen";
import { Suspense } from "react";

export const dynamic = "force-dynamic";

export default function ChatPage() {
  return (
    <Suspense fallback={<main className="chat-main"><p className="muted">Cargando chat…</p></main>}>
      <CoachChatScreen />
    </Suspense>
  );
}
