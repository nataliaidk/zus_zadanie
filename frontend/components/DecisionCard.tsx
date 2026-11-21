"use client";

import { pln } from "@/lib/types";
import { ExplainPanel } from "./ExplainPanel";
import { useGuide } from "./GuideProvider";

function severityWord(severity: string): string {
  if (severity === "block") return "Blokada";
  if (severity === "warning") return "Uwaga";
  return "Info";
}

export function DecisionCard() {
  const { calculation, profile, a11y, explainNode, explanation, closeExplanation, loading } = useGuide();

  if (loading) {
    return (
      <section className="plan-card" aria-live="polite">
        <p>Liczenie…</p>
      </section>
    );
  }

  return (
    <section className="plan-card" aria-live="polite">
      <div className="plan-head">
        <p className="eyebrow">Twój plan</p>
        <h2>{calculation ? "Co Ci przysługuje" : "Tutaj powstanie Twoja osobista ścieżka"}</h2>
      </div>
      {!calculation ? (
        <div className="flex flex-col gap-4">
          <div className="step">
            <span className="step-n">1</span>
            <p>
              <strong>Sytuacja zawodowa</strong>
              <span className="block text-sm">Etat, zlecenie albo JDG</span>
            </p>
          </div>
          <div className="step">
            <span className="step-n">2</span>
            <p>
              <strong>Rodzina</strong>
              <span className="block text-sm">Dzieci, adopcja, Za życiem</span>
            </p>
          </div>
          <div className="step">
            <span className="step-n">3</span>
            <p>
              <strong>Kwota i dokumenty</strong>
              <span className="block text-sm">Podstawa z PDF, wniosek ZAM</span>
            </p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {calculation.blocked && calculation.block_reason ? (
            <p role="alert" className="alert">
              {calculation.block_reason}
            </p>
          ) : null}
          {calculation.monthly_base_pln != null ? (
            <p>
              Podstawa: <strong>{pln(calculation.monthly_base_pln)}</strong>
            </p>
          ) : null}
          <ul className="flex flex-col gap-3">
            {calculation.leaves.map((item, index) => (
              <li key={item.leave_type} className="step">
                <span className="step-n done">{index + 1}</span>
                <p>
                  <strong>{item.title}</strong>
                  {item.weeks != null ? ` — ${item.weeks} tyg.` : null}
                  {item.amount_pln != null ? ` · ${pln(item.amount_pln)}` : null}
                  <span className="block text-sm">
                    {a11y.language === "legal" ? `Węzeł: ${item.graph_node_id}. ` : ""}
                    {item.plain_language}
                  </span>
                </p>
              </li>
            ))}
          </ul>
          <div>
            <h3>Ile i od kogo</h3>
            <p className="mt-2">
              Płatnik: <strong>{calculation.payer === "ZUS" ? "ZUS" : "Twój pracodawca"}</strong>
              {calculation.payer === "ZUS"
                ? " (ZUS wypłaca, bo firma zgłasza do 20 osób)."
                : " (firma powyżej 20 ubezpieczonych sama wypłaca)."}
            </p>
            <p>
              Stawka za całość: {calculation.combined_rate_applied ? "81,5% (wniosek w 21 dni)" : "100% + 70%"}.
            </p>
            <p>
              Aktywny wniosek:{" "}
              {calculation.documents
                .filter((doc) => doc.active)
                .map((doc) => doc.code)
                .join(", ") || "ZAM"}
              . ZUR / ZAO / Z-3b nie są aktywne.
            </p>
            {profile ? (
              <p className="mt-2">
                Forma: {profile.employment_form}, data {profile.birth_date}, dzieci {profile.number_of_children}.
              </p>
            ) : null}
          </div>
          <div>
            <h3>Na co uważać</h3>
            <ul className="mt-3 flex flex-col gap-3">
              {calculation.risks.map((risk) => (
                <li key={risk.code}>
                  <p>
                    <span
                      className={`tag ${risk.severity === "block" ? "block" : risk.severity === "warning" ? "warn" : ""}`}
                    >
                      {severityWord(risk.severity)}
                    </span>{" "}
                    <strong>{risk.title}</strong>
                  </p>
                  <p>{risk.plain_language}</p>
                  <button type="button" className="control mt-2" onClick={() => void explainNode(risk.graph_node_id)}>
                    Skąd ten wynik?
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {explanation ? <ExplainPanel explanation={explanation} onClose={closeExplanation} /> : null}
    </section>
  );
}
