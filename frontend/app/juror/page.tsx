"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { calculateSample, loadSamples, uploadPdf } from "@/lib/api";
import type { CalculationResult, ParentProfile, SampleCase } from "@/lib/types";

export default function JurorPage() {
  const { applyResult } = useGuide();
  const [samples, setSamples] = useState<SampleCase[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [plain, setPlain] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  useEffect(() => {
    void loadSamples()
      .then(setSamples)
      .catch((err: unknown) => setStatus(err instanceof Error ? err.message : "Brak listy spraw."));
  }, []);

  function applyBody(body: Record<string, unknown>, fallback: string) {
    setPlain(typeof body.plain_language === "string" ? body.plain_language : fallback);
    setWarning(typeof body.abolished_form_warning === "string" ? body.abolished_form_warning : null);
    if (body.profile && body.calculation) {
      applyResult(body.profile as ParentProfile, body.calculation as CalculationResult);
    }
  }

  async function onSample(id: string) {
    setStatus("Liczenie sprawy testowej…");
    try {
      const body = await calculateSample(id);
      applyBody(body, "Policzono sprawę testową.");
      setStatus(`Sprawa ${id}. Parser / profil. Kwoty z przepisów.`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Nie policzono sprawy.");
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = (event.currentTarget.elements.namedItem("pdf") as HTMLInputElement).files?.[0];
    if (!file) {
      setStatus("Wybierz plik PDF.");
      return;
    }
    setStatus("Czytam PDF…");
    try {
      const body = await uploadPdf(file);
      applyBody(body, "Odczytano PDF.");
      setStatus(`Typ: ${body.document_type}. Parser: ${body.extraction_method}.`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload nieudany.");
    }
  }

  return (
    <AppShell aside={<DecisionCard />}>
      <h1>Juror — sprawy PDF</h1>
      <p className="mt-2">
        Wybierz sprawę albo wgraj PDF z teczki (ZAM, Z-3, Z-3a, poświadczenie). Parser czyta układ i
        polskie znaki; kwoty liczy silnik, nie czat. Folder na pliki z konkursu:{" "}
        <code>backend/app/data/sprawy</code>.
      </p>
      <h2 className="mt-4">Gotowe sprawy</h2>
      <ul className="mt-2 grid gap-2">
        {samples.map((item) => (
          <li key={item.id} className="flex flex-wrap items-center justify-between gap-4 border p-4">
            <div>
              <strong>{item.title}</strong>
              <p>{item.outcome}</p>
            </div>
            <div className="chip-row">
              <button type="button" className="btn-primary control" onClick={() => void onSample(item.id)}>
                Policz
              </button>
              <a className="control" href={`/api/samples/${item.id}/pdf`}>
                PDF
              </a>
            </div>
          </li>
        ))}
      </ul>
      <form className="mt-4 grid gap-4" onSubmit={onSubmit}>
        <label className="grid gap-2">
          Własny PDF (ZAM, Z-3, ubezpieczenie)
          <input className="control" type="file" name="pdf" accept="application/pdf" />
        </label>
        <button type="submit" className="btn-primary control">
          Policz z PDF
        </button>
      </form>
      <div aria-live="polite">
        {status ? <p className="note mt-4">{status}</p> : null}
        {warning ? <p className="alert mt-4">{warning}</p> : null}
        {plain ? <p className="mt-4 whitespace-pre-wrap">{plain}</p> : null}
      </div>
    </AppShell>
  );
}
