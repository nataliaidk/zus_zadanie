"use client";

import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";

export default function KalkulatorPage() {
  const { plan } = useGuide();

  return (
    <AppShell aside={<DecisionCard />}>
      <h1 className="font-semibold">Kalkulator — oś urlopów</h1>
      <p className="mt-2">
        Oś jest opisana tekstem (kto, jaki urlop, od-do tygodnia). Więcej tabelę dla czytelnika.
      </p>
      <table className="mt-4 w-full border-collapse border">
        <caption className="p-2 text-left">Oś urlopów matka / ojciec</caption>
        <thead>
          <tr>
            <th className="border p-2 text-left">Kto</th>
            <th className="border p-2 text-left">Urlop</th>
            <th className="border p-2 text-left">Od tygodnia</th>
            <th className="border p-2 text-left">Do tygodnia</th>
            <th className="border p-2 text-left">Długość</th>
          </tr>
        </thead>
        <tbody>
          {plan.timeline.map((row) => (
            <tr key={`${row.who}-${row.leave}-${row.fromWeek}`}>
              <td className="border p-2">{row.who}</td>
              <td className="border p-2">{row.leave}</td>
              <td className="border p-2">{row.fromWeek}</td>
              <td className="border p-2">{row.toWeek}</td>
              <td className="border p-2">{row.length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </AppShell>
  );
}
