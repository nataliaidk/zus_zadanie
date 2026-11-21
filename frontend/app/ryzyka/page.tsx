"use client";

import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { ExplainPanel } from "@/components/ExplainPanel";
import { useGuide } from "@/components/GuideProvider";

type RadarRow = {
  id: string;
  title: string;
  status: string;
  action: string;
  detail: string;
  nodeId: string;
};

export default function RyzykaPage() {
  const { calculation, profile, explainNode, explanation, closeExplanation } = useGuide();
  const rows = buildRadar(calculation, profile?.request_days_after_birth ?? null, profile?.b2b_arrears ?? false);

  return (
    <AppShell aside={<DecisionCard />}>
      <h1 className="font-semibold">Radar ryzyk</h1>
      <p className="mt-2">
        Status opisany słowem (otwarte / zamknięte / groźba), nie samym kolorem.
      </p>

      <div className="mt-4 grid gap-4">
        {rows.map((row) => (
          <article key={row.id} className="border p-4">
            <p>
              <strong>{row.status}</strong> | {row.title}
            </p>
            <p className="mt-2">{row.detail}</p>
            <button
              type="button"
              className="mt-2 border px-4 py-2"
              onClick={() => void explainNode(row.nodeId)}
            >
              Skąd ten wynik?
            </button>
          </article>
        ))}
      </div>

      <table className="mt-4 w-full border-collapse border">
        <caption className="p-2 text-left">Radar ryzyk — tabela</caption>
        <thead>
          <tr>
            <th className="border p-2 text-left">Ryzyko</th>
            <th className="border p-2 text-left">Status</th>
            <th className="border p-2 text-left">Co zrobić</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`table-${row.id}`}>
              <td className="border p-2">{row.title}</td>
              <td className="border p-2">{row.status}</td>
              <td className="border p-2">{row.action}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {explanation ? <ExplainPanel explanation={explanation} onClose={closeExplanation} /> : null}
    </AppShell>
  );
}

function buildRadar(
  calculation: ReturnType<typeof useGuide>["calculation"],
  requestDays: number | null,
  arrears: boolean,
): RadarRow[] {
  const waiting = calculation?.waiting_period_days ?? 90;
  const combined = calculation?.combined_rate_applied ?? false;
  const rows: RadarRow[] = [];

  if (combined) {
    rows.push({
      id: "okno",
      title: "81,5% / 21 dni",
      status: "Otwarte",
      action: "Złóż ZAM do terminu",
      detail: "Wniosek do 21 dni po porodzie daje 81,5% za macierzyński i rodzicielski.",
      nodeId: "ryzyko_termin_wniosku_21",
    });
  } else if (requestDays != null && requestDays > 21) {
    rows.push({
      id: "okno",
      title: "81,5% / 21 dni",
      status: "Zamknięte",
      action: "Złóż ZAM — zostaje 100% + 70%",
      detail: "Minęło więcej niż 21 dni. Zostaje 100% + 70%.",
      nodeId: "ryzyko_termin_wniosku_21",
    });
  } else {
    rows.push({
      id: "okno",
      title: "81,5% / 21 dni",
      status: "Info",
      action: "Złóż ZAM do 21 dni po porodzie",
      detail: "Jeśli złożysz wniosek w 21 dni, stawka za całość to 81,5%.",
      nodeId: "ryzyko_termin_wniosku_21",
    });
  }

  if (arrears) {
    rows.push({
      id: "skladki",
      title: "Zaległości składek",
      status: "Groźba odmowy",
      action: "Opłać składki przed wnioskiem",
      detail: "ZUS może nie wypłacić zasiłku, dopóki składki nie są opłacone.",
      nodeId: "ryzyko_zaleglosci_b2b",
    });
  } else {
    rows.push({
      id: "skladki",
      title: "Zaległości składek",
      status: "Brak zaległości",
      action: "Nic",
      detail: "Dokumenty nie wskazują zaległości.",
      nodeId: "ryzyko_zaleglosci_b2b",
    });
  }

  rows.push({
    id: "wyczekiwanie",
    title: `Wyczekiwanie ${waiting} dni`,
    status: "Info",
    action: "Sprawdź, od kiedy jesteś ubezpieczona",
    detail: `Umowa o pracę: 30 dni. Zlecenie / JDG / B2B: 90 dni. U Ciebie: ${waiting} dni.`,
    nodeId: waiting === 30 ? "ryzyko_wyczekiwanie_30" : "ryzyko_wyczekiwanie_90",
  });

  return rows;
}
