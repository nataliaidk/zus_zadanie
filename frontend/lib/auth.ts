import { DEMO_PROFILES } from "./profiles";
import type { ParentProfile, ProfileId } from "./types";

export type LoginMethod = "pue" | "mobywatel" | "pz";

export type DemoAccount = {
  id: Exclude<ProfileId, "guest" | "custom">;
  login: string;
  password: string;
  displayName: string;
  pesel: string;
  peselMasked: string;
  profile: ParentProfile;
};

export const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    id: "anna",
    login: "anna.nowak",
    password: "HasloAnna1",
    displayName: "Anna Nowak",
    pesel: "85031212345",
    peselMasked: "850312*****",
    profile: DEMO_PROFILES.anna,
  },
  {
    id: "piotr",
    login: "piotr.kowalski",
    password: "HasloPiotr1",
    displayName: "Piotr Kowalski",
    pesel: "82051167890",
    peselMasked: "820511*****",
    profile: DEMO_PROFILES.piotr,
  },
  {
    id: "kasia",
    login: "kasia.wisniewska",
    password: "HasloKasia1",
    displayName: "Katarzyna Wiśniewska",
    pesel: "90080411223",
    peselMasked: "900804*****",
    profile: DEMO_PROFILES.kasia,
  },
];

export type AuthUser = {
  id: DemoAccount["id"];
  displayName: string;
  peselMasked: string;
  method: LoginMethod;
};

function digits(value: string): string {
  return value.replace(/\D/g, "");
}

export function findAccountByLogin(login: string, password: string): DemoAccount | null {
  const folded = login.trim().toLowerCase();
  return (
    DEMO_ACCOUNTS.find((item) => item.login === folded && item.password === password) ?? null
  );
}

export function findAccountByPesel(pesel: string, password: string): DemoAccount | null {
  const needle = digits(pesel);
  if (needle.length < 6) return null;
  return (
    DEMO_ACCOUNTS.find(
      (item) => digits(item.pesel).startsWith(needle.slice(0, 6)) && item.password === password,
    ) ?? null
  );
}

export function findAccountById(id: string): DemoAccount | null {
  return DEMO_ACCOUNTS.find((item) => item.id === id) ?? null;
}

export function methodLabel(method: LoginMethod): string {
  if (method === "pue") return "PUE ZUS";
  if (method === "pz") return "Profil zaufany";
  return "mObywatel";
}
