"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { calculate, explain as explainApi } from "@/lib/api";
import { DEMO_PROFILES } from "@/lib/profiles";
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
  setProfileId: (id: ProfileId) => void;
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
  const [profileId, setProfileIdState] = useState<ProfileId>("guest");
  const [profile, setProfile] = useState<ParentProfile | null>(null);
  const [calculation, setCalculation] = useState<CalculationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [a11y, setA11yState] = useState<A11yState>({
    language: "plain",
    hardSituation: false,
    highContrast: false,
    fontScale: 100,
  });

  const plan = useParentPlan(calculation, profile);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.font = String(a11y.fontScale);
    root.dataset.contrast = a11y.highContrast ? "high" : "normal";
    root.dataset.hard = a11y.hardSituation ? "1" : "0";
    root.classList.toggle("contrast", a11y.highContrast);
    root.classList.toggle("hard", a11y.hardSituation);
    root.classList.toggle("scale-125", a11y.fontScale === 125);
    root.classList.toggle("scale-150", a11y.fontScale === 150);
  }, [a11y]);

  const loadDemo = useCallback(async (id: ProfileId) => {
    if (id === "guest" || id === "custom") {
      if (id === "guest") {
        setProfile(null);
        setCalculation(null);
      }
      return;
    }
    const next = DEMO_PROFILES[id];
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

  function setProfileId(id: ProfileId) {
    setProfileIdState(id);
    void loadDemo(id);
  }

  function setA11y(patch: Partial<A11yState>) {
    setA11yState((prev) => ({ ...prev, ...patch }));
  }

  function applyResult(nextProfile: ParentProfile, result: CalculationResult) {
    setProfileIdState("custom");
    setProfile(nextProfile);
    setCalculation(result);
  }

  async function explainNode(nodeId: string) {
    setExplanation(await explainApi(nodeId));
  }

  const value = useMemo(
    () => ({
      profileId,
      setProfileId,
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
    [a11y, calculation, error, explanation, loading, plan, profile, profileId],
  );

  return <GuideContext.Provider value={value}>{children}</GuideContext.Provider>;
}

export function useGuide() {
  const ctx = useContext(GuideContext);
  if (!ctx) throw new Error("useGuide outside GuideProvider");
  return ctx;
}
