"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PROFILE_BUTTONS, profileLabel } from "@/lib/profiles";
import { useGuide } from "./GuideProvider";

const NAV = [
  { href: "/", label: "Start" },
  { href: "/plan", label: "Plan urlopów" },
  { href: "/kalkulator", label: "Kalkulator" },
  { href: "/symulator", label: "Symulator etatu" },
  { href: "/ryzyka", label: "Radar ryzyk" },
  { href: "/juror", label: "Tryb jurora" },
  { href: "/mapa", label: "Mapa przepisów" },
  { href: "/admin", label: "Admin" },
];

export function AppShell({
  children,
  aside,
}: {
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  const pathname = usePathname();
  const { profileId, setProfileId, a11y, setA11y, loading, error } = useGuide();

  return (
    <div className="min-h-screen p-4">
      <header className="border-b pb-4">
        <p className="font-semibold">Zasiłkowy Przewodnik Przyszłego Rodzica</p>
        {a11y.hardSituation ? (
          <p className="mt-2">Tryb trudna sytuacja — bez ozdobników, tylko decyzje i terminy.</p>
        ) : null}

        <div className="mt-4 flex flex-wrap items-center gap-4">
          <p>
            Profil: <strong>{profileLabel(profileId)}</strong>
          </p>
          {PROFILE_BUTTONS.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={profileId === item.id}
              className={`border px-4 py-2 ${profileId === item.id ? "font-semibold" : ""}`}
              onClick={() => setProfileId(item.id)}
            >
              {item.label}
              <span className="block text-sm">{item.hint}</span>
            </button>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-4">
          <button
            type="button"
            className="border px-4 py-2"
            aria-pressed={a11y.language === "plain"}
            onClick={() => setA11y({ language: "plain" })}
          >
            Prosty język
          </button>
          <button
            type="button"
            className="border px-4 py-2"
            aria-pressed={a11y.language === "legal"}
            onClick={() => setA11y({ language: "legal" })}
          >
            Podstawa prawna
          </button>
          <button
            type="button"
            className="border px-4 py-2"
            aria-pressed={a11y.hardSituation}
            onClick={() => setA11y({ hardSituation: !a11y.hardSituation })}
          >
            Trudna sytuacja (strata dziecka / choroba)
          </button>
          <button
            type="button"
            className="border px-4 py-2"
            aria-pressed={a11y.highContrast}
            onClick={() => setA11y({ highContrast: !a11y.highContrast })}
          >
            Wysoki kontrast
          </button>
          {([100, 125, 150] as const).map((scale) => (
            <button
              key={scale}
              type="button"
              className="border px-4 py-2"
              aria-pressed={a11y.fontScale === scale}
              onClick={() => setA11y({ fontScale: scale })}
            >
              Czcionka {scale}%
            </button>
          ))}
        </div>
      </header>

      <nav className="flex flex-wrap gap-4 border-b py-4" aria-label="Główne">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`inline-flex items-center border px-4 py-2 ${pathname === item.href ? "font-semibold" : ""}`}
            aria-current={pathname === item.href ? "page" : undefined}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <p className="sr-only" aria-live="polite">
        {loading ? "Liczenie zasiłku…" : error ? error : ""}
      </p>
      {error ? <p className="mt-4 border p-4">{error}</p> : null}

      {aside ? (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <section className="border p-4">{children}</section>
          <aside className="border p-4">{aside}</aside>
        </div>
      ) : (
        <section className="mt-4 border p-4">{children}</section>
      )}
    </div>
  );
}
