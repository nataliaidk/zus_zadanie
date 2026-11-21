"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { uploadPdf } from "@/lib/api";
import type { CalculationResult, ParentProfile } from "@/lib/types";

export default function JurorPage() {
  const { applyResult } = useGuide();
  const [status, setStatus] = useState<string | null>(null);
  const [plain, setPlain] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [missing, setMissing] = useState<string[]>([]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const file = (form.elements.namedItem("pdf") as HTMLInputElement).files?.[0];
    if (!file) {
      setStatus("Wybierz plik PDF.");
      return;
    }
    setStatus("Czytam PDF…");
    try {
      const body = await uploadPdf(file);
      setPlain(typeof body.plain_language === "string" ? body.plain_language : null);
      setWarning(typeof body.abolished_form_warning === "string" ? body.abolished_form_warning : null);
      setMissing(Array.isArray(body.missing_fields) ? (body.missing_fields as string[]) : []);
      if (body.profile && body.calculation) {
        applyResult(body.profile as ParentProfile, body.calculation as CalculationResult);
        setStatus(`Typ: ${body.document_type}. Parser: ${body.extraction_method}. Policzone.`);
      } else {
        setStatus(`Typ: ${body.document_type}. Brakuje pól do pełnego wyliczenia.`);
      }
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload nieudany.");
    }
  }

  return (
    <AppShell aside={<DecisionCard />}>
      <h1 className="font-semibold">Tryb jurora — wgraj sprawę PDF</h1>
      <p className="mt-2">
        ZAM, Z-3 albo poświadczenie ubezpieczenia. Parser używa regex (zawsze) i LLM tylko gdy jest
        klucz.
      </p>
      <form className="mt-4 grid gap-4" onSubmit={onSubmit}>
        <label className="grid gap-2">
          Plik PDF
          <input className="border p-2" type="file" name="pdf" accept="application/pdf" />
        </label>
        <button type="submit" className="border px-4 py-2">
          Policz z PDF
        </button>
      </form>
      <div aria-live="polite">
        {status ? <p className="mt-4 border p-4">{status}</p> : null}
        {warning ? <p className="mt-4 border p-4">{warning}</p> : null}
        {plain ? <p className="mt-4 whitespace-pre-wrap">{plain}</p> : null}
        {missing.length ? <p className="mt-4">Brakuje: {missing.join(", ")}</p> : null}
      </div>
    </AppShell>
  );
}
