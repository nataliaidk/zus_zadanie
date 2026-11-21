"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { COPY, LINKS } from "@/lib/copy";
import { PROFILE_BUTTONS, profileLabel } from "@/lib/profiles";
import { useGuide } from "./GuideProvider";

const NAV = [
  { href: "/", label: "Start" },
  { href: "/kalkulator", label: "Kalkulator" },
  { href: "/plan", label: "Plan urlopów" },
  { href: "/ciaza", label: "Ciąża" },
  { href: "/dokumenty", label: "Dokumenty" },
  { href: "/uslugi", label: "Usługi" },
  { href: "/wsparcie", label: "Wsparcie" },
  { href: "/ryzyka", label: "Ryzyka" },
  { href: "/mapa", label: "Przepisy" },
  { href: "/juror", label: "Juror" },
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
    <div className="min-h-screen">
      <a href="#tresc" className="skip-link control border bg-[var(--bg-card)] p-4">
        Przejdź do treści
      </a>
      <div className="topbar">
        <p>Przewodnik po urlopach i zasiłkach — listopad 2026</p>
        <div className="chip-row">
          {([100, 125, 150] as const).map((scale) => (
            <button
              key={scale}
              type="button"
              className="control"
              aria-pressed={a11y.fontScale === scale}
              onClick={() => setA11y({ fontScale: scale })}
            >
              A {scale === 100 ? "tekst" : scale === 125 ? "+" : "++"}
            </button>
          ))}
          <button
            type="button"
            className="control"
            aria-pressed={a11y.highContrast}
            onClick={() => setA11y({ highContrast: !a11y.highContrast })}
          >
            Wysoki kontrast
          </button>
        </div>
      </div>
      <header className="site-header">
        <Link href="/" className="brand">
          <span className="brand-mark" aria-hidden="true">
            rd
          </span>
          <span>
            <strong className="block leading-tight">{COPY.appTitle}</strong>
            <span className="block text-sm font-normal">dla przyszłych rodziców</span>
          </span>
        </Link>
        <nav aria-label="Główne">
          <ul className="nav-list">
            {NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="nav-link control"
                  aria-current={pathname === item.href ? "page" : undefined}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="chip-row">
          <button
            type="button"
            className="control"
            aria-pressed={a11y.language === "plain"}
            onClick={() => setA11y({ language: "plain" })}
          >
            Prosty język
          </button>
          <button
            type="button"
            className="control"
            aria-pressed={a11y.language === "legal"}
            onClick={() => setA11y({ language: "legal" })}
          >
            Podstawa prawna
          </button>
        </div>
      </header>
      <div className="wrap">
        <div className="sim-bar" role="group" aria-label="Symulacja logowania">
          <p className="mb-3 text-sm">
            Profil: <strong>{profileLabel(profileId)}</strong> — to tylko symulacja, nie logujemy do ZUS.
          </p>
          <div className="chip-row">
            {PROFILE_BUTTONS.map((item) => (
              <button
                key={item.id}
                type="button"
                className="control"
                aria-pressed={profileId === item.id}
                onClick={() => setProfileId(item.id)}
              >
                {item.label}
                <span className="block text-sm font-normal">{item.hint}</span>
              </button>
            ))}
            <button
              type="button"
              className="control"
              aria-pressed={a11y.hardSituation}
              onClick={() => setA11y({ hardSituation: !a11y.hardSituation })}
            >
              {COPY.hardMode}
            </button>
          </div>
          {a11y.hardSituation ? (
            <p className="mt-3">Tryb wyciszony. Bez grafik. Możesz wrócić do zwykłego widoku w każdej chwili.</p>
          ) : null}
        </div>
      </div>
      <p className="sr-only" aria-live="polite">
        {loading ? "Liczenie zasiłku…" : error ? error : ""}
      </p>
      {error ? (
        <p className="wrap alert" role="alert">
          {error}
        </p>
      ) : null}
      <main id="tresc" className="wrap mt-4">
        {aside ? (
          <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(260px,0.75fr)]">
            <section className="panel">{children}</section>
            <aside>{aside}</aside>
          </div>
        ) : (
          <section className="panel">{children}</section>
        )}
      </main>
      <footer className="site-footer">
        <div className="wrap grid gap-8 md:grid-cols-3">
          <div>
            <h2>Oficjalne strony</h2>
            <ul className="mt-2 grid gap-2">
              {LINKS.map((link) => (
                <li key={link.href}>
                  <a href={link.href} rel="noreferrer">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h2>Wniosek ZAM</h2>
            <p>Od 24.10.2026 ZAM zastępuje ZUR, ZAO i Z-3b. Nie składaj starych formularzy.</p>
          </div>
          <div>
            <h2>Symulacja</h2>
            <p>mObywatel, PUE i wnioski tutaj nic nie wysyłają do ZUS.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
