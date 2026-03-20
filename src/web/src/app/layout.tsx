import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoiceClone — Asistente de Vida Completo para ELA",
  description:
    "Sistema open source de asistencia para personas con ELA: voz clonada, control del ordenador por eye tracking, mensajería — 100% local, 100% privado.",
  keywords: [
    "voice cloning",
    "ELA",
    "ALS",
    "eye tracking",
    "accessibility",
    "open source",
    "asistente ELA",
    "clonación de voz",
    "control por mirada",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" dir="ltr">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        <meta name="theme-color" content="#0A0A0A" />
        <meta name="color-scheme" content="dark" />
      </head>
      <body>
        {/* Skip navigation link — WCAG requirement */}
        <a href="#main-content" className="skip-link">
          Saltar al contenido principal
        </a>
        <div id="main-content">
          {children}
        </div>
      </body>
    </html>
  );
}
