import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fitness Coach — Diego",
  description: "Coaching dashboard (vChallenges 21K, mmB 2027, Letras, 70.3 Cartagena)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
