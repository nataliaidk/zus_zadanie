import type { Metadata } from "next";
import { Source_Sans_3 } from "next/font/google";
import { GuideProvider } from "@/components/GuideProvider";
import "./globals.css";

const font = Source_Sans_3({
  subsets: ["latin", "latin-ext"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Zasiłkowy Przewodnik Przyszłego Rodzica",
  description: "Urlopy i zasiłki dla przyszłych rodziców. Stan prawny: listopad 2026.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl" className={font.variable}>
      <body className={font.className}>
        <GuideProvider>{children}</GuideProvider>
      </body>
    </html>
  );
}
