"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { runSim } from "@/lib/api";
import { LINKS } from "@/lib/copy";

const ACTIONS = [
  { kind: "mobywatel", label: "Pobierz dane z mObywatel" },
  { kind: "insurance", label: "Pobierz ubezpieczenie z ZUS" },
  { kind: "arrears", label: "Zaświadczenie o zaległościach (JDG)" },
  { kind: "ezla", label: "e-ZLA kod B" },
  { kind: "pue", label: "PUE / eZUS" },
  { kind: "application", label: "Wypełnij i wyślij ZAM" },
  { kind: "rsc", label: "Odpis aktu urodzenia (RSC)" },
];

export default function UslugiPage() {
  const { profile } = useGuide();
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(kind: string) {
    setError(null);
    try {
      setResult(await runSim(kind, profile));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Symulacja nieudana.");
    }
  }

  return (
    <AppShell aside={<DecisionCard />}>
      <h1>Usługi elektroniczne</h1>
      <p className="note mt-2">
        Te czynności są pokazane tak, jak wyglądałyby na koncie — nic nie jest wysyłane do ZUS.
      </p>
      <div className="mt-4 grid gap-3">
        {ACTIONS.map((item) => (
          <button key={item.kind} type="button" className="control" onClick={() => void run(item.kind)}>
            {item.label}
          </button>
        ))}
      </div>
      <div aria-live="polite" className="mt-4">
        {error ? (
          <p className="alert" role="alert">
            {error}
          </p>
        ) : null}
        {result ? (
          <article className="panel">
            <p className="badge">{String(result.banner ?? "SYMULACJA")}</p>
            <pre className="mt-4 whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
          </article>
        ) : null}
      </div>
      <h2 className="mt-4">Linki zewnętrzne (prawdziwe)</h2>
      <ul className="mt-2 grid gap-2">
        {LINKS.map((link) => (
          <li key={link.href}>
            <a className="control" href={link.href} rel="noreferrer">
              {link.label}
            </a>
          </li>
        ))}
        <li>
          <a className="control" href="https://www.gov.pl/web/cyfryzacja/rejestr-stanu-cywilnego" rel="noreferrer">
            Rejestr stanu cywilnego
          </a>
        </li>
      </ul>
    </AppShell>
  );
}
