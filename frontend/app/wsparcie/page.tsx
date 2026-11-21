"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { loadCharities } from "@/lib/api";
import type { Charity } from "@/lib/types";

const FILTERS = [
  { id: "all", label: "Wszystkie" },
  { id: "stillbirth", label: "Martwe urodzenie" },
  { id: "miscarriage", label: "Poronienie" },
  { id: "preterm", label: "Wcześniak" },
  { id: "ill_child", label: "Ciężko chore dziecko" },
];

export default function WsparciePage() {
  const [items, setItems] = useState<Charity[]>([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadCharities()
      .then(setItems)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Nie wczytano listy."));
  }, []);

  const shown = items.filter((item) => filter === "all" || item.situations.includes(filter));

  return (
    <AppShell>
      <h1>Organizacje pomocowe</h1>
      <p className="mt-2">
        To nie zastępuje zasiłku. Lista dla sytuacji straty, wcześniaka i ciężkiej choroby dziecka.
      </p>
      <div className="chip-row mt-4" role="group" aria-label="Filtr sytuacji">
        {FILTERS.map((item) => (
          <button
            key={item.id}
            type="button"
            className="control"
            aria-pressed={filter === item.id}
            onClick={() => setFilter(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {error ? (
        <p className="alert mt-4" role="alert">
          {error}
        </p>
      ) : null}
      <ul className="mt-4 grid gap-4">
        {shown.map((item) => (
          <li key={item.id} className="panel">
            <h2>{item.name}</h2>
            <p className="mt-2">{item.help}</p>
            <a className="control mt-3" href={item.url} rel="noreferrer">
              Strona organizacji
            </a>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}
