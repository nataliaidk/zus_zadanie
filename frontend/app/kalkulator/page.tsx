"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { calculate } from "@/lib/api";
import type { EmploymentForm, FamilyPath, ParentProfile } from "@/lib/types";
import { pln } from "@/lib/types";

type FormState = {
  family_path: FamilyPath;
  employment_form: EmploymentForm;
  company_insured_above_20: boolean;
  birth_date: string;
  number_of_children: number;
  child_age_years: string;
  school_deferred: boolean;
  za_zyciem_certificate: boolean;
  preterm: boolean;
  stillbirth: boolean;
  benefit_base_pln: string;
  request_days_after_birth: string;
  combine_work_fraction: "0" | "0.25" | "0.5";
  parental_together: boolean;
  insured: boolean;
  insurance_days: string;
  rehab_after_sickness: boolean;
  employer_bankruptcy: boolean;
  unlawful_dismissal: boolean;
  job_ended_before_birth: boolean;
  apparent_contract: boolean;
  mother_hospitalized: boolean;
  b2b_arrears: boolean;
  part_time: boolean;
};

const EMPTY: FormState = {
  family_path: "birth",
  employment_form: "umowa_o_prace",
  company_insured_above_20: false,
  birth_date: "2026-11-01",
  number_of_children: 1,
  child_age_years: "",
  school_deferred: false,
  za_zyciem_certificate: false,
  preterm: false,
  stillbirth: false,
  benefit_base_pln: "5200",
  request_days_after_birth: "0",
  combine_work_fraction: "0",
  parental_together: false,
  insured: true,
  insurance_days: "",
  rehab_after_sickness: false,
  employer_bankruptcy: false,
  unlawful_dismissal: false,
  job_ended_before_birth: false,
  apparent_contract: false,
  mother_hospitalized: false,
  b2b_arrears: false,
  part_time: false,
};

function fromProfile(profile: ParentProfile | null): FormState {
  if (!profile) return EMPTY;
  return {
    ...EMPTY,
    family_path: profile.family_path ?? "birth",
    employment_form: profile.employment_form,
    company_insured_above_20: profile.company_insured_above_20,
    birth_date: profile.birth_date,
    number_of_children: profile.number_of_children,
    child_age_years: profile.child_age_years != null ? String(profile.child_age_years) : "",
    school_deferred: profile.school_deferred ?? false,
    za_zyciem_certificate: profile.za_zyciem_certificate ?? false,
    preterm: profile.preterm ?? false,
    stillbirth: profile.stillbirth ?? false,
    benefit_base_pln: profile.benefit_base_pln != null ? String(profile.benefit_base_pln) : "",
    request_days_after_birth:
      profile.request_days_after_birth != null ? String(profile.request_days_after_birth) : "",
    combine_work_fraction:
      profile.combine_work_fraction === 0.5 ? "0.5" : profile.combine_work_fraction === 0.25 ? "0.25" : "0",
    parental_together: profile.parental_together ?? false,
    insured: profile.insured !== false,
    insurance_days: profile.insurance_days != null ? String(profile.insurance_days) : "",
    rehab_after_sickness: profile.rehab_after_sickness ?? false,
    employer_bankruptcy: profile.employer_bankruptcy ?? false,
    unlawful_dismissal: profile.unlawful_dismissal ?? false,
    job_ended_before_birth: profile.job_ended_before_birth ?? false,
    apparent_contract: profile.apparent_contract ?? false,
    mother_hospitalized: profile.mother_hospitalized ?? false,
    b2b_arrears: profile.b2b_arrears ?? false,
    part_time: profile.part_time ?? false,
  };
}

function toProfile(form: FormState): ParentProfile {
  return {
    employment_form: form.employment_form,
    company_insured_above_20: form.company_insured_above_20,
    birth_date: form.birth_date,
    number_of_children: form.number_of_children,
    family_path: form.family_path,
    child_age_years: form.child_age_years === "" ? null : Number(form.child_age_years),
    school_deferred: form.school_deferred,
    za_zyciem_certificate: form.za_zyciem_certificate,
    preterm: form.preterm,
    stillbirth: form.stillbirth,
    benefit_base_pln: form.benefit_base_pln === "" ? null : Number(form.benefit_base_pln),
    request_days_after_birth:
      form.request_days_after_birth === "" ? null : Number(form.request_days_after_birth),
    combine_work_fraction: Number(form.combine_work_fraction),
    parental_together: form.parental_together,
    insured: form.insured,
    insurance_days: form.insurance_days === "" ? null : Number(form.insurance_days),
    rehab_after_sickness: form.rehab_after_sickness,
    employer_bankruptcy: form.employer_bankruptcy,
    unlawful_dismissal: form.unlawful_dismissal,
    job_ended_before_birth: form.job_ended_before_birth,
    apparent_contract: form.apparent_contract,
    mother_hospitalized: form.mother_hospitalized,
    b2b_arrears: form.b2b_arrears,
    part_time: form.part_time,
  };
}

export default function KalkulatorPage() {
  const { profile, calculation, applyResult, plan } = useGuide();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    setForm(fromProfile(profile));
  }, [profile]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const next = toProfile(form);
    setStatus("Liczenie…");
    try {
      const result = await calculate(next);
      applyResult(next, result);
      setStatus("Policzono. Kwoty wynikają z przepisów (listopad 2026), nie z czatu.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Nie udało się policzyć.");
    }
  }

  function patch<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <AppShell aside={<DecisionCard />}>
      <h1>Kalkulator urlopów i kwot</h1>
      <p className="mt-2">
        Jedna decyzja w każdej grupie. Silnik liczy wymiar i kwotę dla obojga rodziców.
      </p>
      <form className="mt-4 grid gap-4" onSubmit={onSubmit}>
        <fieldset className="grid gap-4">
          <legend>Rodzina</legend>
          <label className="grid gap-2">
            Ścieżka
            <select
              className="control"
              value={form.family_path}
              onChange={(event) => patch("family_path", event.target.value as FamilyPath)}
            >
              <option value="birth">Poród</option>
              <option value="adoption">Adopcja</option>
              <option value="foster">Rodzina zastępcza niezawodowa</option>
            </select>
          </label>
          <label className="grid gap-2">
            Ile dzieci (przy jednym porodzie / przyjęciu)
            <input
              className="control"
              type="number"
              min={1}
              max={8}
              value={form.number_of_children}
              onChange={(event) => patch("number_of_children", Number(event.target.value))}
            />
          </label>
          {form.family_path !== "birth" ? (
            <>
              <label className="grid gap-2">
                Wiek dziecka (lata)
                <input
                  className="control"
                  type="number"
                  min={0}
                  max={17}
                  value={form.child_age_years}
                  onChange={(event) => patch("child_age_years", event.target.value)}
                />
              </label>
              {form.family_path === "foster" ? (
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.school_deferred}
                    onChange={(event) => patch("school_deferred", event.target.checked)}
                  />
                  Odroczenie obowiązku szkolnego (limit 10 lat)
                </label>
              ) : null}
            </>
          ) : null}
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.za_zyciem_certificate}
              onChange={(event) => patch("za_zyciem_certificate", event.target.checked)}
            />
            Zaświadczenie „Za życiem”
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.preterm}
              onChange={(event) => patch("preterm", event.target.checked)}
            />
            Wcześniak / hospitalizacja po porodzie
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.stillbirth}
              onChange={(event) => patch("stillbirth", event.target.checked)}
            />
            Martwe urodzenie
          </label>
        </fieldset>
        <fieldset className="grid gap-4">
          <legend>Praca i podstawa</legend>
          <label className="grid gap-2">
            Jak pracujesz
            <select
              className="control"
              value={form.employment_form}
              onChange={(event) => patch("employment_form", event.target.value as EmploymentForm)}
            >
              <option value="umowa_o_prace">Umowa o pracę</option>
              <option value="zlecenie">Zlecenie</option>
              <option value="jdg">JDG</option>
              <option value="b2b">B2B</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.company_insured_above_20}
              onChange={(event) => patch("company_insured_above_20", event.target.checked)}
            />
            Pracodawca zgłaszał powyżej 20 osób
          </label>
          <label className="grid gap-2">
            Twoja podstawa wymiaru (zł / miesiąc)
            <input
              className="control"
              type="number"
              min={0}
              step="0.01"
              value={form.benefit_base_pln}
              onChange={(event) => patch("benefit_base_pln", event.target.value)}
            />
          </label>
          <label className="grid gap-2">
            Ile dni po porodzie złożysz ZAM (puste = nie wiadomo)
            <input
              className="control"
              type="number"
              min={0}
              value={form.request_days_after_birth}
              onChange={(event) => patch("request_days_after_birth", event.target.value)}
            />
          </label>
        </fieldset>
        <fieldset className="grid gap-4">
          <legend>Urlop rodzicielski</legend>
          <label className="grid gap-2">
            Łączenie z pracą
            <select
              className="control"
              value={form.combine_work_fraction}
              onChange={(event) =>
                patch("combine_work_fraction", event.target.value as FormState["combine_work_fraction"])
              }
            >
              <option value="0">Bez pracy</option>
              <option value="0.25">Praca 1/4 etatu</option>
              <option value="0.5">Praca 1/2 etatu</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.parental_together}
              onChange={(event) => patch("parental_together", event.target.checked)}
            />
            Oboje rodzice korzystają jednocześnie
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.mother_hospitalized}
              onChange={(event) => patch("mother_hospitalized", event.target.checked)}
            />
            Matka w szpitalu — ojciec może przejąć wcześniej niż po 14 tyg.
          </label>
        </fieldset>
        <fieldset className="grid gap-4">
          <legend>Ciąża i uprawnienia</legend>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.insured}
              onChange={(event) => patch("insured", event.target.checked)}
            />
            Jest ubezpieczenie chorobowe
          </label>
          <label className="grid gap-2">
            Dni ubezpieczenia (puste = wystarczy)
            <input
              className="control"
              type="number"
              min={0}
              value={form.insurance_days}
              onChange={(event) => patch("insurance_days", event.target.value)}
            />
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.rehab_after_sickness}
              onChange={(event) => patch("rehab_after_sickness", event.target.checked)}
            />
            Po 270 dniach choroby — świadczenie rehabilitacyjne
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.employer_bankruptcy}
              onChange={(event) => patch("employer_bankruptcy", event.target.checked)}
            />
            Upadłość / likwidacja pracodawcy w ciąży
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.unlawful_dismissal}
              onChange={(event) => patch("unlawful_dismissal", event.target.checked)}
            />
            Nielegalne zwolnienie (wyrok)
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.job_ended_before_birth}
              onChange={(event) => patch("job_ended_before_birth", event.target.checked)}
            />
            Umowa skończyła się przed porodem
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.apparent_contract}
              onChange={(event) => patch("apparent_contract", event.target.checked)}
            />
            Umowa albo JDG tylko dla zasiłku
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.b2b_arrears}
              onChange={(event) => patch("b2b_arrears", event.target.checked)}
            />
            Zaległości składek
          </label>
        </fieldset>
        <button type="submit" className="btn-primary control">
          Policz wymiar i kwoty
        </button>
      </form>
      <p className="mt-4" aria-live="polite">
        {status}
      </p>
      {calculation ? (
        <div className="table-wrap mt-4">
          <table>
            <caption className="p-2 text-left">Urlopy — wymiar i kwota</caption>
            <thead>
              <tr>
                <th>Urlop</th>
                <th>Tygodnie</th>
                <th>Kalendarz</th>
                <th>Stawka</th>
                <th>Kwota</th>
              </tr>
            </thead>
            <tbody>
              {calculation.leaves.map((item) => (
                <tr key={item.leave_type}>
                  <td>{item.title}</td>
                  <td>{item.weeks ?? "—"}</td>
                  <td>{item.calendar_weeks ?? item.weeks ?? "—"}</td>
                  <td>{item.rate_percent}%</td>
                  <td>{pln(item.amount_pln)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      <div className="table-wrap mt-4">
        <table>
          <caption className="p-2 text-left">Oś urlopów matka / ojciec</caption>
          <thead>
            <tr>
              <th>Kto</th>
              <th>Urlop</th>
              <th>Od tyg.</th>
              <th>Do tyg.</th>
              <th>Długość</th>
            </tr>
          </thead>
          <tbody>
            {plan.timeline.map((row) => (
              <tr key={`${row.who}-${row.leave}-${row.fromWeek}`}>
                <td>{row.who}</td>
                <td>{row.leave}</td>
                <td>{row.fromWeek}</td>
                <td>{row.toWeek}</td>
                <td>{row.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
