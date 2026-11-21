import type { ParentProfile, ProfileId } from "./types";

export const PROFILE_BUTTONS: { id: ProfileId; label: string; hint: string }[] = [
  { id: "guest", label: "Niezalogowany", hint: "Niezalogowany" },
  { id: "anna", label: "Anna — etat", hint: "mObywatel" },
  { id: "piotr", label: "Piotr — B2B", hint: "mObywatel" },
  { id: "kasia", label: "Kasia — zlecenie", hint: "PUE eZUS" },
];

export const DEMO_PROFILES: Record<Exclude<ProfileId, "guest" | "custom">, ParentProfile> = {
  anna: {
    employment_form: "umowa_o_prace",
    company_insured_above_20: false,
    birth_date: "2026-11-01",
    number_of_children: 1,
    preterm: false,
    za_zyciem_certificate: false,
    part_time: false,
    b2b_arrears: false,
    request_days_after_birth: 0,
    benefit_base_pln: 5200,
    insured: true,
  },
  piotr: {
    employment_form: "b2b",
    company_insured_above_20: false,
    birth_date: "2026-11-01",
    number_of_children: 1,
    preterm: false,
    za_zyciem_certificate: false,
    part_time: false,
    b2b_arrears: true,
    request_days_after_birth: 30,
    benefit_base_pln: 8900,
    insured: true,
  },
  kasia: {
    employment_form: "zlecenie",
    company_insured_above_20: false,
    birth_date: "2026-11-01",
    number_of_children: 1,
    preterm: false,
    za_zyciem_certificate: false,
    part_time: false,
    b2b_arrears: false,
    request_days_after_birth: 0,
    benefit_base_pln: 4100,
    insured: true,
  },
};

export function profileLabel(id: ProfileId): string {
  if (id === "anna") return "Anna — etat (mObywatel)";
  if (id === "piotr") return "Piotr — B2B (mObywatel)";
  if (id === "kasia") return "Kasia — zlecenie (PUE eZUS)";
  if (id === "custom") return "Z czatu / PDF";
  return "Niezalogowany (bez logowania)";
}

export const NODE_TYPE_LABEL: Record<string, string> = {
  status_ubezpieczenia: "Status",
  zdarzenie: "Zdarzenie",
  swiadczenie: "Świadczenie",
  dokument: "Dokument",
  ryzyko: "Ryzyko",
  przepis: "Przepis",
};
