import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoiceClone — Preserva tu voz. Para siempre.",
  description:
    "Plataforma open source de clonación de voz para personas con ELA y enfermedades que afectan al habla. 100% gratis, 100% privado, 100% local.",
  keywords: [
    "voice cloning",
    "ELA",
    "ALS",
    "speech disability",
    "accessibility",
    "open source",
    "clonación de voz",
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
      </head>
      <body>
        {/* Skip navigation link — WCAG requirement */}
        <a href="#main-content" className="skip-link">
          Saltar al contenido principal
        </a>
        <main id="main-content" role="main">
          {children}
        </main>
      </body>
    </html>
  );
}
