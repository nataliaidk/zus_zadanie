import type { Metadata } from "next";
import { GuideProvider } from "@/components/GuideProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zasiłkowy Przewodnik Przyszłego Rodzica",
  description: "Wireframe WCAG — HackNation ZUS, stan prawny listopad 2026.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body>
        <GuideProvider>{children}</GuideProvider>
      </body>
    </html>
  );
}
