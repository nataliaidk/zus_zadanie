"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { COPY, LINKS } from "@/lib/copy";
import { methodLabel } from "@/lib/auth";
import { LoginDialog } from "./LoginDialog";
import { useGuide } from "./GuideProvider";

const NAV = [
  { href: "/", label: "Start" },
  { href: "/kalkulator", label: "Kalkulator" },
  { href: "/plan", label: "Plan urlopów" },
  { href: "/ciaza", label: "Zasiłek w ciąży" },
  { href: "/dokumenty", label: "Dokumenty" },
  { href: "/uslugi", label: "Usługi" },
  { href: "/wsparcie", label: "Wsparcie" },
  { href: "/mapa", label: "Przepisy" },
];

export function AppShell({
  children,
  aside,
}: {
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user, logout, a11y, setA11y, loading, error } = useGuide();
  const [loginOpen, setLoginOpen] = useState(false);

  return (
    <div className="min-h-screen">
      <a href="#tresc" className="skip-link control border bg-[var(--bg-card)] p-4">
        Przejdź do treści
      </a>
      <div className="chrome">
      <div className="gov-bar">
        <p>Wersja demonstracyjna · stan prawny listopad 2026</p>
        <div className="chip-row" role="toolbar" aria-label="Ułatwienia">
          {([100, 125, 150] as const).map((scale) => (
            <button
              key={scale}
              type="button"
              className="control ghost"
              aria-pressed={a11y.fontScale === scale}
              onClick={() => setA11y({ fontScale: scale })}
            >
              A {scale === 100 ? "tekst" : scale === 125 ? "+" : "++"}
            </button>
          ))}
          <button
            type="button"
            className="control ghost"
            aria-pressed={a11y.highContrast}
            onClick={() => setA11y({ highContrast: !a11y.highContrast })}
          >
            Wysoki kontrast
          </button>
          <button
            type="button"
            className="control ghost"
            aria-pressed={a11y.language === "plain"}
            onClick={() => setA11y({ language: "plain" })}
          >
            Prosty język
          </button>
          <button
            type="button"
            className="control ghost"
            aria-pressed={a11y.language === "legal"}
            onClick={() => setA11y({ language: "legal" })}
          >
            Podstawa prawna
          </button>
        </div>
      </div>
      <header className="site-header">
        <Link href="/" className="brand">
          <span className="brand-mark" aria-hidden="true">
            Z
          </span>
          <span>
            <strong className="block leading-tight">{COPY.appTitle}</strong>
            <span className="block text-sm font-normal">przyszłego rodzica</span>
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
        {user ? (
          <div className="session">
            <p>
              <span className="sr-only">Zalogowano: </span>
              <strong>{user.displayName}</strong>
              <span className="block text-sm font-normal">
                {methodLabel(user.method)} · PESEL {user.peselMasked}
              </span>
            </p>
            <button type="button" className="control" onClick={logout}>
              Wyloguj
            </button>
          </div>
        ) : (
          <button type="button" className="btn-login control" onClick={() => setLoginOpen(true)}>
            Zaloguj się
          </button>
        )}
      </header>
      </div>
      <p className="sr-only" aria-live="polite">
        {loading ? "Liczenie zasiłku…" : error ? error : `Wielkość tekstu ${a11y.fontScale} procent.`}
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
            <h2>Autor strony</h2>
            <p>{COPY.author}</p>
          </div>
          <div>
            <h2>Kod źródłowy</h2>
            <p>
              <a href={COPY.github} rel="noreferrer">
                github.com/nataliaidk/zus_zadanie
              </a>
            </p>
            <p className="mt-4">
              <Link href="/ryzyka">Ryzyka</Link>
              {" · "}
              <Link href="/juror">Dla jurorów</Link>
              {" · "}
              <Link href="/admin">Admin</Link>
            </p>
          </div>
        </div>
      </footer>
      {loginOpen ? <LoginDialog onClose={() => setLoginOpen(false)} /> : null}
    </div>
  );
}
