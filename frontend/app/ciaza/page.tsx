"use client";

import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { pln } from "@/lib/types";

export default function CiazaPage() {
  const { calculation, profile } = useGuide();
  const items = calculation?.pregnancy ?? [];

  return (
    <AppShell aside={<DecisionCard />}>
      <h1>Ciąża — choroba, rehab, macierzyński po utracie pracy</h1>
      <p className="mt-2">
        Kod B to 100% podstawy, maksymalnie 270 dni. Wyczekiwanie: 30 dni na etacie, 90 na zleceniu i
        JDG. Zaloguj się albo policz w kalkulatorze.
      </p>
      {!items.length ? (
        <p className="note mt-4">Najpierw zaloguj się albo policz w kalkulatorze.</p>
      ) : null}
      <div className="mt-4 grid gap-4" aria-live="polite">
        {items.map((item) => (
          <article key={item.code} className={item.entitled ? "panel" : "alert"}>
            <h2>
              {item.entitled ? "Przysługuje" : "Nie przysługuje"} — {item.title}
            </h2>
            <p className="mt-2">{item.plain_language}</p>
            {item.rate_percent != null ? <p>Stawka: {item.rate_percent}%</p> : null}
            {item.max_days != null ? <p>Maks. dni: {item.max_days}</p> : null}
            {item.amount_pln != null ? <p>Szacunek: {pln(item.amount_pln)}</p> : null}
          </article>
        ))}
      </div>
      <div className="table-wrap mt-4">
        <table>
          <caption className="p-2 text-left">Świadczenia w ciąży</caption>
          <thead>
            <tr>
              <th>Świadczenie</th>
              <th>Status</th>
              <th>Stawka</th>
              <th>Opis</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`t-${item.code}`}>
                <td>{item.title}</td>
                <td>{item.entitled ? "Przysługuje" : "Nie przysługuje"}</td>
                <td>{item.rate_percent ?? "—"}</td>
                <td>{item.plain_language}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {profile ? (
        <p className="mt-4">
          Forma: {profile.employment_form}. Wyczekiwanie w wyniku: {calculation?.waiting_period_days} dni.
        </p>
      ) : null}
    </AppShell>
  );
}
