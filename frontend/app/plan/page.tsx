"use client";

import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";

export default function PlanPage() {
  const { profile, plan } = useGuide();

  return (
    <AppShell aside={<DecisionCard />}>
      <h1>Plan urlopów matki i ojca</h1>
      <p className="mt-2">
        Poka-yoke: nielegalny podział jest blokowany i wyjaśniany. Pierwsze 14 tygodni
        macierzyńskiego — matka. 9 tygodni rodzicielskiego — każdy rodzic osobno.
      </p>

      {!profile ? (
        <p className="note mt-4">
          Wybierz profil Anny, Piotra albo Kasi albo dokończ czat na Start.
        </p>
      ) : null}

      {plan.pokaMessage ? (
        <p className="alert mt-4" role="alert" aria-live="assertive">
          {plan.pokaMessage}
        </p>
      ) : null}

      <div className="table-wrap mt-4">
      <table>
        <caption className="p-2 text-left">Podział tygodni (tabela dla czytników ekranu)</caption>
        <thead>
          <tr>
            <th className="border p-2 text-left">Urlop</th>
            <th className="border p-2 text-left">Matka</th>
            <th className="border p-2 text-left">Ojciec</th>
            <th className="border p-2 text-left">Suma / limit</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="border p-2">Macierzyński</td>
            <td className="border p-2">{plan.maternityMother} tyg.</td>
            <td className="border p-2">{plan.maternityFather} tyg.</td>
            <td className="border p-2">{plan.maternityTotal} tyg.</td>
          </tr>
          <tr>
            <td className="border p-2">Rodzicielski</td>
            <td className="border p-2">{plan.parentalMother} tyg.</td>
            <td className="border p-2">{plan.parentalFather} tyg.</td>
            <td className="border p-2">{plan.parentalTotal} tyg.</td>
          </tr>
          <tr>
            <td className="border p-2">Ojcowski</td>
            <td className="border p-2">0</td>
            <td className="border p-2">{plan.paternityWeeks} tyg. (14 dni)</td>
            <td className="border p-2">{plan.paternityWeeks} tyg.</td>
          </tr>
        </tbody>
      </table>
      </div>

      <div className="mt-4 grid gap-4">
        <label className="grid gap-2">
          Tygodnie macierzyńskiego dla matki (minimum 14)
          <input
            className="control"
            type="number"
            min={14}
            max={plan.maternityTotal}
            value={plan.maternityMother}
            onChange={(event) => plan.setMaternityMother(Number(event.target.value))}
          />
        </label>
        <label className="grid gap-2">
          Tygodnie macierzyńskiego dla ojca
          <input className="control" type="number" value={plan.maternityFather} readOnly />
        </label>
        <label className="grid gap-2">
          Tygodnie rodzicielskiego dla matki
          <input
            className="control"
            type="number"
            min={9}
            max={plan.parentalTotal - 9}
            value={plan.parentalMother}
            onChange={(event) => plan.setParentalSplit(Number(event.target.value))}
          />
        </label>
        <label className="grid gap-2">
          Tygodnie rodzicielskiego dla ojca
          <input className="control" type="number" value={plan.parentalFather} readOnly />
        </label>
        <button type="button" className="control" onClick={plan.tryGiveFirst14ToFather}>
          Spróbuj oddać pierwsze 14 tygodni ojcu (test poka-yoke)
        </button>
      </div>

      <h2 className="mt-4 font-semibold">Checklista z terminami</h2>
      <ul className="mt-2 grid gap-2">
        {plan.checklist.map((item) => (
          <li key={item} className="note">
            {item}
          </li>
        ))}
      </ul>
      <p className="mt-4">
        Skąd ten wynik? — użyj przycisków na karcie po prawej (ścieżka grafu wiedzy).
      </p>
    </AppShell>
  );
}
