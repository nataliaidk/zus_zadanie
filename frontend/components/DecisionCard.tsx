"use client";

import { useGuide } from "./GuideProvider";
import { ExplainPanel } from "./ExplainPanel";

function pct(value: number): string {
  return String(value).replace(".", ",");
}

function severityWord(severity: string): string {
  if (severity === "block") return "Blokada";
  if (severity === "warning") return "Ostrzeżenie";
  return "Info";
}

export function DecisionCard() {
  const { calculation, profile, a11y, explainNode, explanation, closeExplanation, loading } = useGuide();

  if (loading) {
    return <p aria-live="polite">Liczenie…</p>;
  }

  if (!calculation) {
    return (
      <div>
        <h2 className="font-semibold">Co Ci przysługuje</h2>
        <p className="mt-2">
          Odpowiedzi z lewej strony albo profil z belki wypełnią tę kartę. Nic jeszcze nie policzono.
        </p>
      </div>
    );
  }

  const maternity = calculation.leaves.find((item) => item.leave_type === "macierzynski");
  const parental = calculation.leaves.find((item) => item.leave_type === "rodzicielski");
  const rates = maternity && parental
    ? calculation.combined_rate_applied
      ? `Stawki: macierzyński ${pct(maternity.rate_percent)}%, rodzicielski ${pct(parental.rate_percent)}% (81,5% za całość — wniosek w 21 dni).`
      : `Stawki: macierzyński ${pct(maternity.rate_percent)}%, rodzicielski ${pct(parental.rate_percent)}% (100% + 70%).`
    : "";
  const active = calculation.documents.filter((doc) => doc.active).map((doc) => doc.code).join(", ");

  return (
    <div>
      <h2 className="font-semibold">Co Ci przysługuje</h2>
      {calculation.blocked && calculation.block_reason ? (
        <p className="mt-2 border p-4" role="alert">
          {calculation.block_reason}
        </p>
      ) : null}

      <div className="mt-4 grid gap-4" aria-live="polite">
        {calculation.leaves.map((item) => (
          <article key={item.leave_type} className="border p-4">
            <h3 className="font-semibold">
              {item.title} — {item.weeks ?? "?"} tyg.
            </h3>
            <p className="mt-2">
              {a11y.language === "legal"
                ? `Węzeł grafu: ${item.graph_node_id}. ${item.plain_language}`
                : item.plain_language}
            </p>
          </article>
        ))}
      </div>

      <article className="mt-4 border p-4">
        <h3 className="font-semibold">Ile i od kogo</h3>
        <p className="mt-2">
          Płatnik: <strong>{calculation.payer}</strong>
          {calculation.payer === "ZUS"
            ? ' (nie „płatnik składek” — ZUS wypłaca, bo firma zgłasza do 20 osób).'
            : " (Twój pracodawca wypłaca, bo zgłaszał powyżej 20 osób)."}
        </p>
        <p>{rates}</p>
        <p>Aktywny wniosek: {active || "ZAM"}. ZUR / ZAO / Z-3b nie są aktywne.</p>
        {profile ? (
          <p className="mt-2">
            Forma: {profile.employment_form}, poród {profile.birth_date}, dzieci {profile.number_of_children}.
          </p>
        ) : null}
      </article>

      <section className="mt-4">
        <h3 className="font-semibold">Na co uważać (Radar ryzyk)</h3>
        <div className="mt-2 grid gap-4">
          {calculation.risks.map((risk) => (
            <article key={risk.code} className="border p-4">
              <p>
                <span className="font-semibold">{severityWord(risk.severity)}</span> {risk.title}
              </p>
              <p className="mt-2">{risk.plain_language}</p>
              <button
                type="button"
                className="mt-2 border px-4 py-2"
                onClick={() => void explainNode(risk.graph_node_id)}
              >
                Skąd ten wynik?
              </button>
            </article>
          ))}
        </div>
      </section>

      {explanation ? (
        <ExplainPanel explanation={explanation} onClose={closeExplanation} />
      ) : null}
    </div>
  );
}
