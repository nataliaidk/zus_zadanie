"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { calculate, explain as explainApi } from "@/lib/api";
import {
  findAccountByLogin,
  findAccountByPesel,
  type AuthUser,
  type LoginMethod,
} from "@/lib/auth";
import { useParentPlan } from "@/hooks/useParentPlan";
import type {
  A11yState,
  CalculationResult,
  ExplainResponse,
  ParentProfile,
  ProfileId,
} from "@/lib/types";

type GuideContextValue = {
  profileId: ProfileId;
  user: AuthUser | null;
  loginPassword: (login: string, password: string, method: LoginMethod) => boolean;
  loginMobywatel: (pesel: string, password: string) => boolean;
  logout: () => void;
  profile: ParentProfile | null;
  calculation: CalculationResult | null;
  loading: boolean;
  error: string | null;
  a11y: A11yState;
  setA11y: (patch: Partial<A11yState>) => void;
  applyResult: (profile: ParentProfile, result: CalculationResult) => void;
  explainNode: (nodeId: string) => Promise<void>;
  explanation: ExplainResponse | null;
  closeExplanation: () => void;
  plan: ReturnType<typeof useParentPlan>;
};

const GuideContext = createContext<GuideContextValue | null>(null);

export function GuideProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [profileId, setProfileId] = useState<ProfileId>("guest");
  const [profile, setProfile] = useState<ParentProfile | null>(null);
  const [calculation, setCalculation] = useState<CalculationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [a11y, setA11yState] = useState<A11yState>({
    language: "plain",
    highContrast: false,
    fontScale: 100,
  });

  const plan = useParentPlan(calculation, profile);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.font = String(a11y.fontScale);
    root.dataset.contrast = a11y.highContrast ? "high" : "normal";
    root.classList.toggle("contrast", a11y.highContrast);
    root.classList.toggle("scale-125", a11y.fontScale === 125);
    root.classList.toggle("scale-150", a11y.fontScale === 150);
  }, [a11y]);

  const loadProfile = useCallback(async (next: ParentProfile) => {
    setProfile(next);
    setLoading(true);
    setError(null);
    try {
      setCalculation(await calculate(next));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się policzyć.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loginPassword = useCallback(
    (login: string, password: string, method: LoginMethod) => {
      const account = findAccountByLogin(login, password);
      if (!account) return false;
      setUser({
        id: account.id,
        displayName: account.displayName,
        peselMasked: account.peselMasked,
        method,
      });
      setProfileId(account.id);
      void loadProfile(account.profile);
      return true;
    },
    [loadProfile],
  );

  const loginMobywatel = useCallback(
    (pesel: string, password: string) => {
      const account = findAccountByPesel(pesel, password);
      if (!account) return false;
      setUser({
        id: account.id,
        displayName: account.displayName,
        peselMasked: account.peselMasked,
        method: "mobywatel",
      });
      setProfileId(account.id);
      void loadProfile(account.profile);
      return true;
    },
    [loadProfile],
  );

  function logout() {
    setUser(null);
    setProfileId("guest");
    setProfile(null);
    setCalculation(null);
  }

  function setA11y(patch: Partial<A11yState>) {
    setA11yState((prev) => ({ ...prev, ...patch }));
  }

  function applyResult(nextProfile: ParentProfile, result: CalculationResult) {
    setProfileId("custom");
    setProfile(nextProfile);
    setCalculation(result);
  }

  async function explainNode(nodeId: string) {
    setExplanation(await explainApi(nodeId));
  }

  const value = useMemo(
    () => ({
      profileId,
      user,
      loginPassword,
      loginMobywatel,
      logout,
      profile,
      calculation,
      loading,
      error,
      a11y,
      setA11y,
      applyResult,
      explainNode,
      explanation,
      closeExplanation: () => setExplanation(null),
      plan,
    }),
    [
      a11y,
      calculation,
      error,
      explanation,
      loading,
      loginMobywatel,
      loginPassword,
      plan,
      profile,
      profileId,
      user,
    ],
  );

  return <GuideContext.Provider value={value}>{children}</GuideContext.Provider>;
}

export function useGuide() {
  const ctx = useContext(GuideContext);
  if (!ctx) throw new Error("useGuide outside GuideProvider");
  return ctx;
}
