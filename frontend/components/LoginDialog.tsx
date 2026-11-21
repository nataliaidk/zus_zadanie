"use client";

import { FormEvent, useEffect, useId, useState } from "react";
import { DEMO_ACCOUNTS, type LoginMethod } from "@/lib/auth";
import { useGuide } from "./GuideProvider";

export function LoginDialog({ onClose }: { onClose: () => void }) {
  const { loginPue, loginMobywatel } = useGuide();
  const titleId = useId();
  const [tab, setTab] = useState<LoginMethod>("pue");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function onPue(event: FormEvent) {
    event.preventDefault();
    const ok = loginPue(login, password);
    if (!ok) {
      setError("Nieprawidłowy login albo hasło. Sprawdź dane demonstracyjne poniżej.");
      return;
    }
    onClose();
  }

  function onMobywatel(id: string) {
    loginMobywatel(id);
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
            <h2 id={titleId}>Zaloguj się do konta</h2>
          </div>
          <button type="button" className="control" onClick={onClose}>
            Zamknij
          </button>
        </div>
        <p className="mt-2 text-sm">
          To konto demonstracyjne na potrzeby konkursu. Nic nie idzie do prawdziwego ZUS ani mObywatela.
        </p>
        <div className="chip-row mt-4" role="tablist" aria-label="Sposób logowania">
          <button
            type="button"
            role="tab"
            className="control"
            aria-selected={tab === "pue"}
            aria-pressed={tab === "pue"}
            onClick={() => setTab("pue")}
          >
            PUE ZUS
          </button>
          <button
            type="button"
            role="tab"
            className="control"
            aria-selected={tab === "mobywatel"}
            aria-pressed={tab === "mobywatel"}
            onClick={() => setTab("mobywatel")}
          >
            mObywatel
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
              Zaloguj
            </button>
          </form>
        ) : (
          <div className="mt-4 grid gap-3">
            <p>Wybierz konto, którym chcesz się zalogować (symulacja mObywatel).</p>
            {DEMO_ACCOUNTS.map((account) => (
              <button
                key={account.id}
                type="button"
                className="choice control"
                onClick={() => onMobywatel(account.id)}
              >
                <span>
                  <strong className="block">{account.displayName}</strong>
                  <span className="block text-sm font-normal">PESEL {account.peselMasked}</span>
                </span>
              </button>
            ))}
          </div>
        )}
        <details className="mt-4">
          <summary className="control">Dane demonstracyjne (dla jurorów)</summary>
          <ul className="mt-3 grid gap-2 text-sm">
            {DEMO_ACCOUNTS.map((account) => (
              <li key={account.id}>
                {account.displayName}: login <code>{account.login}</code>, hasło{" "}
                <code>{account.password}</code>
              </li>
            ))}
          </ul>
        </details>
      </div>
    </div>
  );
}
