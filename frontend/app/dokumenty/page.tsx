"use client";

import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { LINKS } from "@/lib/copy";

export default function DokumentyPage() {
  const { calculation, plan } = useGuide();
  const filing = calculation?.filing ?? [];
  const docs = calculation?.documents ?? [];

  return (
    <AppShell aside={<DecisionCard />}>
      <h1>Dokumenty, terminy, gdzie złożyć</h1>
      <p className="mt-2">
        Od 24 października 2026 jeden wniosek <strong>ZAM</strong>. ZUR, ZAO i Z-3b są zniesione.
        Płatnik powyżej 20 osób wypłaca sam; mniejszy przekazuje Z-3 / Z-3a do ZUS.
      </p>
      <ul className="mt-4 grid gap-2">
        {plan.checklist.map((item) => (
          <li key={item} className="note">
            {item}
          </li>
        ))}
      </ul>
      <div className="table-wrap mt-4">
        <table>
          <caption className="p-2 text-left">Gdzie i do kiedy</caption>
          <thead>
            <tr>
              <th>Gdzie</th>
              <th>Co</th>
              <th>Termin</th>
              <th>Wyjaśnienie</th>
            </tr>
          </thead>
          <tbody>
            {filing.map((item) => (
              <tr key={`${item.where}-${item.what}`}>
                <td>{item.where}</td>
                <td>{item.what}</td>
                <td>{item.deadline}</td>
                <td>{item.plain_language}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 className="mt-4">Wnioski</h2>
      <ul className="mt-2 grid gap-2">
        {docs.map((doc) => (
          <li key={doc.code} className="panel">
            <strong>
              {doc.code}
              {doc.active ? " — aktywny" : " — nie składaj"}
            </strong>
            <p>{doc.plain_language}</p>
            {doc.replaced_by ? <p>Zastąpiony przez {doc.replaced_by}.</p> : null}
          </li>
        ))}
      </ul>
      <h2 className="mt-4">Oficjalne strony</h2>
      <ul className="mt-2 grid gap-2">
        {LINKS.map((link) => (
          <li key={link.href}>
            <a className="control" href={link.href} rel="noreferrer">
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}
