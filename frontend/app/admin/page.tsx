"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { loadParams, saveParams } from "@/lib/api";

type Rates = {
  maternity: number;
  parental: number;
  combined_if_request_within_deadline: number;
  paternity: number;
  supplementary_maternity: number;
};

export default function AdminPage() {
  const [raw, setRaw] = useState<Record<string, unknown> | null>(null);
  const [rates, setRates] = useState<Rates | null>(null);
  const [waiting30, setWaiting30] = useState(30);
  const [waiting90, setWaiting90] = useState(90);
  const [maxima, setMaxima] = useState("20");
  const [employerAbove, setEmployerAbove] = useState(20);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    void loadParams()
      .then((body) => {
        setRaw(body);
        setRates(body.rates_percent as Rates);
        const waiting = body.waiting_period_days as Record<string, number>;
        setWaiting30(waiting.umowa_o_prace);
        setWaiting90(waiting.zlecenie);
        const weeks = body.maternity_weeks_by_children as Record<string, number>;
        setMaxima(String(weeks["1"]));
        setEmployerAbove(Number(body.employer_pays_if_insured_above));
      })
      .catch((err: unknown) => setStatus(err instanceof Error ? err.message : "Nie wczytano."));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!raw || !rates) return;
    const waiting = {
      ...(raw.waiting_period_days as Record<string, number>),
      umowa_o_prace: waiting30,
      zlecenie: waiting90,
      jdg: waiting90,
      b2b: waiting90,
    };
    const weeks = {
      ...(raw.maternity_weeks_by_children as Record<string, number>),
      "1": Number(maxima),
    };
    const payload = {
      ...raw,
      rates_percent: rates,
      waiting_period_days: waiting,
      maternity_weeks_by_children: weeks,
      employer_pays_if_insured_above: employerAbove,
    };
    try {
      const saved = await saveParams(payload);
      setRaw(saved);
      setStatus("Zapisano stawki i limity.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Zapis nieudany.");
    }
  }

  return (
    <AppShell>
      <h1>Admin — stawki i maksima</h1>
      <p className="mt-2">Zmiana tu idzie do params.json. Silnik nie zgaduje kwot.</p>
      {!rates ? <p className="mt-4">Wczytuję…</p> : (
        <form className="mt-4 grid gap-4" onSubmit={onSubmit}>
          <fieldset className="grid gap-4">
            <legend>Stawki %</legend>
            {(
              [
                ["maternity", "Macierzyński"],
                ["parental", "Rodzicielski"],
                ["combined_if_request_within_deadline", "81,5% za całość"],
                ["paternity", "Ojcowski"],
                ["supplementary_maternity", "Uzupełniający"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="grid gap-2">
                {label}
                <input
                  className="control"
                  type="number"
                  step="0.1"
                  value={rates[key]}
                  onChange={(event) => setRates({ ...rates, [key]: Number(event.target.value) })}
                />
              </label>
            ))}
          </fieldset>
          <fieldset className="grid gap-4">
            <legend>Limity</legend>
            <label className="grid gap-2">
              Wyczekiwanie etat (dni)
              <input
                className="control"
                type="number"
                value={waiting30}
                onChange={(event) => setWaiting30(Number(event.target.value))}
              />
            </label>
            <label className="grid gap-2">
              Wyczekiwanie zlecenie / JDG (dni)
              <input
                className="control"
                type="number"
                value={waiting90}
                onChange={(event) => setWaiting90(Number(event.target.value))}
              />
            </label>
            <label className="grid gap-2">
              Macierzyński przy 1 dziecku (tyg.)
              <input
                className="control"
                type="number"
                value={maxima}
                onChange={(event) => setMaxima(event.target.value)}
              />
            </label>
            <label className="grid gap-2">
              Płatnik wypłaca, gdy ubezpieczonych powyżej
              <input
                className="control"
                type="number"
                value={employerAbove}
                onChange={(event) => setEmployerAbove(Number(event.target.value))}
              />
            </label>
          </fieldset>
          <button type="submit" className="btn-primary control">
            Zapisz
          </button>
        </form>
      )}
      <p className="mt-4" aria-live="polite">
        {status}
      </p>
    </AppShell>
  );
}
