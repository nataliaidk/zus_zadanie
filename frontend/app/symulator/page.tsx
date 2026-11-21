"use client";

import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";

export default function SymulatorPage() {
  const { plan } = useGuide();

  return (
    <AppShell aside={<DecisionCard />}>
      <h1 className="font-semibold">Symulator etatu</h1>
      <p className="mt-2">
        Jeśli łączysz urlop z pracą na 1/2 etatu, urlop jest na pozostałą połowę i kalendarzowo się
        wydłuża.
      </p>
      <label className="mt-4 grid gap-2">
        Ile tygodni puli rodzicielskiej chcesz łączyć z pracą na 1/2 etatu?
        <input
          className="border p-2"
          type="number"
          min={0}
          max={plan.parentalTotal}
          value={plan.halfTimeWeeks}
          onChange={(event) => plan.setHalfTimeWeeks(Number(event.target.value))}
        />
      </label>
      <table className="mt-4 w-full border-collapse border">
        <caption className="p-2 text-left">Porównanie puli i kalendarza</caption>
        <thead>
          <tr>
            <th className="border p-2 text-left">Pozycja</th>
            <th className="border p-2 text-left">Tygodnie</th>
            <th className="border p-2 text-left">Opis</th>
          </tr>
        </thead>
        <tbody>
          {plan.halfTime.map((row) => (
            <tr key={row.label}>
              <td className="border p-2">{row.label}</td>
              <td className="border p-2">{row.weeks}</td>
              <td className="border p-2">{row.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </AppShell>
  );
}
