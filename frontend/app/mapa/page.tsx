"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { ExplainPanel } from "@/components/ExplainPanel";
import { useGuide } from "@/components/GuideProvider";
import { loadGraph } from "@/lib/api";
import { NODE_TYPE_LABEL } from "@/lib/profiles";
import type { GraphEdge, GraphNode } from "@/lib/types";

export default function MapaPage() {
  const { explainNode, explanation, closeExplanation, a11y } = useGuide();
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadGraph()
      .then((body) => {
        setNodes(body.nodes);
        setEdges(body.edges);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Nie udało się wczytać przepisów.");
      });
  }, []);

  const groups = groupByType(nodes);

  return (
    <AppShell>
      <h1 className="font-semibold">Przepisy</h1>
      <p className="mt-2">
        Przegląd reguł, z których korzysta przewodnik (stan na listopad 2026). Typ jest napisany
        słowem, nie samym kolorem.
      </p>
      {error ? <p className="mt-4">{error}</p> : null}

      {Object.entries(groups).map(([type, group]) => (
        <section key={type} className="mt-4">
          <h2 className="font-semibold">{NODE_TYPE_LABEL[type] ?? type}</h2>
          <ul className="mt-2 grid gap-2">
            {group.map((node) => (
              <li key={node.id}>
                <button
                  type="button"
                  className="w-full border px-4 py-2 text-left"
                  onClick={() => void explainNode(node.id)}
                >
                  <strong>{node.title}</strong>
                  <span className="block">
                    {a11y.language === "legal" ? node.legal_basis : node.plain_language}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <table className="mt-4 w-full border-collapse border">
        <caption className="p-2 text-left">Przepisy — tabela dostępna</caption>
        <thead>
          <tr>
            <th className="border p-2 text-left">Typ</th>
            <th className="border p-2 text-left">Tytuł</th>
            <th className="border p-2 text-left">Prosty język</th>
            <th className="border p-2 text-left">Podstawa prawna</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((node) => (
            <tr key={node.id}>
              <td className="border p-2">{NODE_TYPE_LABEL[node.type] ?? node.type}</td>
              <td className="border p-2">
                <button type="button" className="border px-4 py-2" onClick={() => void explainNode(node.id)}>
                  {node.title}
                </button>
              </td>
              <td className="border p-2">{node.plain_language}</td>
              <td className="border p-2">{node.legal_basis}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <table className="mt-4 w-full border-collapse border">
        <caption className="p-2 text-left">Powiązania między przepisami</caption>
        <thead>
          <tr>
            <th className="border p-2 text-left">Od</th>
            <th className="border p-2 text-left">Do</th>
            <th className="border p-2 text-left">Relacja</th>
            <th className="border p-2 text-left">Opis</th>
          </tr>
        </thead>
        <tbody>
          {edges.map((edge) => (
            <tr key={`${edge.source}-${edge.target}-${edge.relation}`}>
              <td className="border p-2">{edge.source}</td>
              <td className="border p-2">{edge.target}</td>
              <td className="border p-2">{edge.relation}</td>
              <td className="border p-2">{edge.plain_language}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {explanation ? <ExplainPanel explanation={explanation} onClose={closeExplanation} /> : null}
    </AppShell>
  );
}

function groupByType(nodes: GraphNode[]): Record<string, GraphNode[]> {
  const out: Record<string, GraphNode[]> = {};
  for (const node of nodes) {
    (out[node.type] ??= []).push(node);
  }
  return out;
}
