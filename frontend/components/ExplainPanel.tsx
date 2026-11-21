"use client";

import type { ExplainResponse } from "@/lib/types";
import { NODE_TYPE_LABEL } from "@/lib/profiles";

export function ExplainPanel({
  explanation,
  onClose,
}: {
  explanation: ExplainResponse;
  onClose: () => void;
}) {
  return (
    <section className="mt-4 border p-4" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="font-semibold">{explanation.question}</h3>
        <button type="button" className="border px-4 py-2" onClick={onClose}>
          Zamknij
        </button>
      </div>
      <ol className="mt-4 list-decimal pl-6">
        {explanation.narrative.map((line, index) => (
          <li key={`${index}-${line}`}>{line}</li>
        ))}
      </ol>
      <table className="mt-4 w-full border-collapse border">
        <caption className="p-2 text-left font-semibold">Przepisy</caption>
        <thead>
          <tr>
            <th className="border p-2 text-left">Typ</th>
            <th className="border p-2 text-left">Tytuł</th>
            <th className="border p-2 text-left">Prosty język</th>
            <th className="border p-2 text-left">Podstawa prawna</th>
          </tr>
        </thead>
        <tbody>
          {explanation.nodes.map((node) => (
            <tr key={node.id}>
              <td className="border p-2">{NODE_TYPE_LABEL[node.type] ?? node.type}</td>
              <td className="border p-2">{node.title}</td>
              <td className="border p-2">{node.plain_language}</td>
              <td className="border p-2">{node.legal_basis}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
