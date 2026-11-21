import { DEMO_PROFILES } from "./profiles";
import type { ParentProfile, ProfileId } from "./types";

export type LoginMethod = "pue" | "mobywatel";

export type DemoAccount = {
  id: Exclude<ProfileId, "guest" | "custom">;
  login: string;
  password: string;
  displayName: string;
  peselMasked: string;
  profile: ParentProfile;
};

export const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    id: "anna",
    login: "anna.nowak",
    password: "HasloAnna1",
    displayName: "Anna Nowak",
    peselMasked: "850312*****",
    profile: DEMO_PROFILES.anna,
  },
  {
    id: "piotr",
    login: "piotr.kowalski",
    password: "HasloPiotr1",
    displayName: "Piotr Kowalski",
    peselMasked: "820511*****",
    profile: DEMO_PROFILES.piotr,
  },
  {
    id: "kasia",
    login: "kasia.wisniewska",
    password: "HasloKasia1",
    displayName: "Katarzyna Wiśniewska",
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

export function findAccountByLogin(login: string, password: string): DemoAccount | null {
  const folded = login.trim().toLowerCase();
  return (
    DEMO_ACCOUNTS.find((item) => item.login === folded && item.password === password) ?? null
  );
}

export function findAccountById(id: string): DemoAccount | null {
  return DEMO_ACCOUNTS.find((item) => item.id === id) ?? null;
}
