"use client";

import { FormEvent, useEffect, useId, useState } from "react";
import { DEMO_ACCOUNTS, type LoginMethod } from "@/lib/auth";
import { useGuide } from "./GuideProvider";

export function LoginDialog({ onClose }: { onClose: () => void }) {
  const { loginPassword, loginMobywatel } = useGuide();
  const titleId = useId();
  const [tab, setTab] = useState<LoginMethod>("pue");
  const [login, setLogin] = useState("");
  const [pesel, setPesel] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function fail() {
    setError("Nie udało się zalogować. Sprawdź dane demonstracyjne poniżej — to nie jest prawdziwy ZUS.");
  }

  function onPue(event: FormEvent) {
    event.preventDefault();
    if (!loginPassword(login, password, "pue")) {
      fail();
      return;
    }
    onClose();
  }

  function onPz(event: FormEvent) {
    event.preventDefault();
    if (!loginPassword(login, password, "pz")) {
      fail();
      return;
    }
    onClose();
  }

  function onMobywatel(event: FormEvent) {
    event.preventDefault();
    if (!loginMobywatel(pesel, password)) {
      fail();
      return;
    }
    onClose();
  }

  return (
    <div className="dialog-backdrop" role="presentation" onClick={onClose}>
      <div
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Logowanie</p>
            <h2 id={titleId}>Zaloguj się</h2>
          </div>
          <button type="button" className="control" onClick={onClose}>
            Zamknij
          </button>
        </div>
        <p className="mt-2 text-sm">
          Wersja konkursowa. Logowanie nic nie wysyła do ZUS, mObywatela ani Profilu zaufanego.
        </p>
        <div className="chip-row mt-4" role="tablist" aria-label="Sposób logowania">
          <button
            type="button"
            role="tab"
            className="control"
            aria-selected={tab === "pue"}
            aria-pressed={tab === "pue"}
            onClick={() => {
              setTab("pue");
              setError(null);
            }}
          >
            PUE ZUS
          </button>
          <button
            type="button"
            role="tab"
            className="control"
            aria-selected={tab === "mobywatel"}
            aria-pressed={tab === "mobywatel"}
            onClick={() => {
              setTab("mobywatel");
              setError(null);
            }}
          >
            mObywatel
          </button>
          <button
            type="button"
            role="tab"
            className="control"
            aria-selected={tab === "pz"}
            aria-pressed={tab === "pz"}
            onClick={() => {
              setTab("pz");
              setError(null);
            }}
          >
            Profil zaufany
          </button>
        </div>

        {tab === "pue" ? (
          <form className="mt-4 grid gap-4" onSubmit={onPue}>
            <label className="grid gap-2">
              Login
              <input
                className="control"
                autoComplete="username"
                value={login}
                onChange={(event) => setLogin(event.target.value)}
              />
            </label>
            <label className="grid gap-2">
              Hasło
              <input
                className="control"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            {error ? (
              <p className="alert" role="alert">
                {error}
              </p>
            ) : null}
            <button type="submit" className="btn-primary control">
              Zaloguj przez PUE
            </button>
          </form>
        ) : null}

        {tab === "pz" ? (
          <form className="mt-4 grid gap-4" onSubmit={onPz}>
            <p>Profil zaufany — podaj login i hasło, tak jak na login.gov.pl.</p>
            <label className="grid gap-2">
              Login
              <input
                className="control"
                autoComplete="username"
                value={login}
                onChange={(event) => setLogin(event.target.value)}
              />
            </label>
            <label className="grid gap-2">
              Hasło
              <input
                className="control"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            {error ? (
              <p className="alert" role="alert">
                {error}
              </p>
            ) : null}
            <button type="submit" className="btn-primary control">
              Zaloguj przez Profil zaufany
            </button>
          </form>
        ) : null}

        {tab === "mobywatel" ? (
          <form className="mt-4 grid gap-4" onSubmit={onMobywatel}>
            <p>Aplikacja mObywatel — wpisz PESEL i kod z aplikacji.</p>
            <label className="grid gap-2">
              PESEL
              <input
                className="control"
                inputMode="numeric"
                autoComplete="off"
                value={pesel}
                onChange={(event) => setPesel(event.target.value)}
              />
            </label>
            <label className="grid gap-2">
              Kod z aplikacji
              <input
                className="control"
                type="password"
                autoComplete="one-time-code"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            {error ? (
              <p className="alert" role="alert">
                {error}
              </p>
            ) : null}
            <button type="submit" className="btn-primary control">
              Potwierdź w mObywatel
            </button>
          </form>
        ) : null}

        <details className="mt-4">
          <summary className="control">Dane demonstracyjne (dla jurorów)</summary>
          <ul className="mt-3 grid gap-2 text-sm">
            {DEMO_ACCOUNTS.map((account) => (
              <li key={account.id}>
                {account.displayName}, PESEL {account.peselMasked}: login{" "}
                <code>{account.login}</code>, hasło / kod <code>{account.password}</code>
              </li>
            ))}
          </ul>
        </details>
      </div>
    </div>
  );
}
