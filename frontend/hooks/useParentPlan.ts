"use client";

import { useEffect, useMemo, useState } from "react";
import type { CalculationResult, ParentProfile } from "@/lib/types";

export type TimelineRow = {
  who: string;
  leave: string;
  fromWeek: number;
  toWeek: number;
  length: number;
};

export type HalfTimeRow = {
  label: string;
  weeks: number;
  note: string;
};

const MOTHER_ONLY = 14;
const FATHER_RESERVED = 9;

export function useParentPlan(calculation: CalculationResult | null, profile: ParentProfile | null) {
  const maternityTotal = calculation?.leaves.find((item) => item.leave_type === "macierzynski")?.weeks ?? 20;
  const parentalTotal = calculation?.leaves.find((item) => item.leave_type === "rodzicielski")?.weeks ?? 41;
  const paternityWeeks = calculation?.leaves.find((item) => item.leave_type === "ojcowski")?.weeks ?? 2;

  const [maternityMother, setMaternityMotherState] = useState(20);
  const [parentalMother, setParentalMother] = useState(20);
  const [parentalFather, setParentalFather] = useState(21);
  const [pokaMessage, setPokaMessage] = useState<string | null>(null);
  const [halfTimeWeeks, setHalfTimeWeeks] = useState(10);

  useEffect(() => {
    if (!calculation) return;
    setMaternityMotherState(maternityTotal);
    const motherParental = Math.min(parentalTotal - FATHER_RESERVED, 20);
    setParentalMother(motherParental);
    setParentalFather(parentalTotal - motherParental);
    setPokaMessage(null);
  }, [calculation, maternityTotal, parentalTotal]);

  const maternityFather = Math.max(0, maternityTotal - maternityMother);

  function setMaternityMother(weeks: number) {
    if (weeks < MOTHER_ONLY) {
      setPokaMessage(
        `Nie zapisano tej zmiany. Pierwsze ${MOTHER_ONLY} tygodni urlopu macierzyńskiego są dla matki. Nie można ich oddać ojcu (wyjątki: szpital, niezdolność do samodzielnej egzystencji, zgon lub porzucenie).`,
      );
      return;
    }
    if (weeks > maternityTotal) {
      setPokaMessage(`Nie zapisano. Macierzyński ma ${maternityTotal} tygodni.`);
      return;
    }
    setPokaMessage(null);
    setMaternityMotherState(weeks);
  }

  function tryGiveFirst14ToFather() {
    setMaternityMother(maternityTotal - MOTHER_ONLY);
  }

  function setParentalSplit(motherWeeks: number) {
    const maxMother = parentalTotal - FATHER_RESERVED;
    const minMother = FATHER_RESERVED;
    if (motherWeeks < minMother) {
      setPokaMessage(
        `Nie zapisano. Każdy rodzic ma ${FATHER_RESERVED} tygodni rodzicielskiego tylko dla siebie.`,
      );
      return;
    }
    if (motherWeeks > maxMother) {
      setPokaMessage(
        `Nie zapisano. Ojciec musi zachować ${FATHER_RESERVED} tygodni nieprzenoszalnych.`,
      );
      return;
    }
    setPokaMessage(null);
    setParentalMother(motherWeeks);
    setParentalFather(parentalTotal - motherWeeks);
  }

  const checklist = useMemo(() => {
    const items: string[] = [];
    if (profile?.birth_date) {
      const deadline = addDays(profile.birth_date, 21);
      items.push(
        calculation?.combined_rate_applied
          ? `Złóż wniosek ZAM do ${deadline}, jeśli chcesz 81,5% za całość.`
          : `Okno 21 dni na 81,5% minęło (termin był ${deadline}). Zostaje 100% + 70%.`,
      );
    } else {
      items.push("Złóż wniosek ZAM do 21 dni po porodzie, jeśli chcesz 81,5% za całość.");
    }
    if (profile?.employment_form === "umowa_o_prace" && calculation?.payer === "ZUS") {
      items.push("Pracodawca dokłada Z-3 (etat) albo Z-3a (zlecenie) do ZUS.");
    } else if (profile?.employment_form === "zlecenie") {
      items.push("Pracodawca dokłada Z-3 (etat) albo Z-3a (zlecenie) do ZUS.");
    } else {
      items.push("Wniosek ZAM składasz do ZUS (B2B / JDG — bez Z-3).");
    }
    items.push("Nie składaj ZUR, ZAO ani Z-3b. Od 24.10.2026 jest ZAM.");
    return items;
  }, [calculation, profile]);

  const timeline: TimelineRow[] = useMemo(() => {
    const rows: TimelineRow[] = [];
    let cursor = 1;
    if (maternityMother > 0) {
      rows.push({
        who: "Matka",
        leave: "Macierzyński",
        fromWeek: cursor,
        toWeek: cursor + maternityMother - 1,
        length: maternityMother,
      });
      cursor += maternityMother;
    }
    if (maternityFather > 0) {
      rows.push({
        who: "Ojciec",
        leave: "Macierzyński",
        fromWeek: cursor,
        toWeek: cursor + maternityFather - 1,
        length: maternityFather,
      });
      cursor += maternityFather;
    }
    if (parentalMother > 0) {
      rows.push({
        who: "Matka",
        leave: "Rodzicielski",
        fromWeek: cursor,
        toWeek: cursor + parentalMother - 1,
        length: parentalMother,
      });
      cursor += parentalMother;
    }
    if (parentalFather > 0) {
      rows.push({
        who: "Ojciec",
        leave: "Rodzicielski",
        fromWeek: cursor,
        toWeek: cursor + parentalFather - 1,
        length: parentalFather,
      });
      cursor += parentalFather;
    }
    if (paternityWeeks > 0) {
      rows.push({
        who: "Ojciec",
        leave: "Ojcowski",
        fromWeek: cursor,
        toWeek: cursor + paternityWeeks - 1,
        length: paternityWeeks,
      });
    }
    return rows;
  }, [maternityFather, maternityMother, parentalFather, parentalMother, paternityWeeks]);

  const usedHalf = Math.min(Math.max(0, halfTimeWeeks), parentalTotal);
  const calendarHalf = usedHalf * 2;
  const restPool = parentalTotal - usedHalf;
  const halfTime: HalfTimeRow[] = [
    {
      label: "Pula rodzicielska",
      weeks: parentalTotal,
      note: `Z silnika (${parentalTotal} / 43 / 65 / 67)`,
    },
    {
      label: "Zużyte przy 1/2 etatu",
      weeks: usedHalf,
      note: "Tyle schodzi z puli",
    },
    {
      label: "Kalendarz przy 1/2 etatu",
      weeks: calendarHalf,
      note: "Podwójny czas (praca 50%)",
    },
    {
      label: "Reszta puli (bez pracy)",
      weeks: restPool,
      note: "Kalendarz = pula",
    },
    {
      label: "Razem w kalendarzu",
      weeks: calendarHalf + restPool,
      note: "Czas z dzieckiem łącznie",
    },
  ];

  return {
    maternityTotal,
    parentalTotal,
    paternityWeeks,
    maternityMother,
    maternityFather,
    parentalMother,
    parentalFather,
    pokaMessage,
    halfTimeWeeks,
    setHalfTimeWeeks,
    setMaternityMother,
    setParentalSplit,
    tryGiveFirst14ToFather,
    checklist,
    timeline,
    halfTime,
  };
}

function addDays(iso: string, days: number): string {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
