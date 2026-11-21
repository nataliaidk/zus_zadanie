"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { useGuidedChat } from "@/hooks/useGuidedChat";
import { COPY } from "@/lib/copy";

const STEP_HINTS: { test: string; title: string }[] = [
  { test: "Jak pracujesz", title: "Twoja sytuacja zawodowa" },
  { test: "pracodawca zgłaszał", title: "Kto wypłaci zasiłek" },
  { test: "Ile dzieci", title: "Twoja rodzina" },
  { test: "przedwcześnie", title: "Pobyt w szpitalu" },
  { test: "Za życiem", title: "Zaświadczenie Za życiem" },
  { test: "część etatu", title: "Wymiar etatu" },
  { test: "zaległości", title: "Składki" },
  { test: "21 dni", title: "Ważne terminy" },
  { test: "data urodzenia", title: "Data porodu" },
];

function ChoiceIcon({ id }: { id: string }) {
  const common = { width: 20, height: 20, fill: "none", stroke: "currentColor", strokeWidth: 1.8 };
  if (id === "umowa_o_prace") {
    return (
      <svg {...common} viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 3h7l4 4v14H7z" />
        <path d="M14 3v4h4M9 13h6M9 17h4" />
      </svg>
    );
  }
  return (
    <svg {...common} viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" />
    </svg>
  );
}

export default function HomePage() {
  const { applyResult, a11y } = useGuide();
  const chat = useGuidedChat(applyResult);
  const [message, setMessage] = useState("");
  const index = chat.question ? STEP_HINTS.findIndex((item) => chat.question!.includes(item.test)) : 0;
  const n = index >= 0 ? index + 1 : 1;
  const title = index >= 0 ? STEP_HINTS[index].title : "Rozmowa";

  function onAsk(event: FormEvent) {
    event.preventDefault();
    void chat.ask(message);
    setMessage("");
  }

  return (
    <AppShell aside={<DecisionCard />}>
      <p className="badge">{COPY.badge}</p>
      <h1 className="hero mt-4">
        {COPY.heroTitle} <span className="accent">{COPY.heroAccent}</span>
      </h1>
      <p className="mt-4 max-w-xl">{COPY.heroLead}</p>
      <p className="mt-4 flex items-center gap-3">
        <span className="step-n done" aria-hidden="true">
          {n}
        </span>
        <span>
          <span className="eyebrow block">
            Krok {n} z {STEP_HINTS.length}
          </span>
          <strong>{title}</strong>
        </span>
      </p>
      {chat.question ? <h2 className="mt-4 text-2xl">{chat.question}</h2> : null}
      {chat.helper ? <p className="mt-2">{chat.helper}</p> : null}
      {chat.buttons.length ? (
        <div className="mt-4 grid gap-3" role="group" aria-label="Gotowe odpowiedzi">
          {chat.buttons.map((button) => (
            <button
              key={button.id}
              type="button"
              className="choice control"
              disabled={chat.loading}
              onClick={() => void chat.answerButton(button.id)}
            >
              <span className="choice-ico">
                <ChoiceIcon id={button.id} />
              </span>
              <span>{button.label}</span>
              <span className="choice-radio" aria-hidden="true" />
            </button>
          ))}
        </div>
      ) : null}
      <div aria-live="polite">
        {chat.answer ? (
          <article className="note mt-4">
            <p className="whitespace-pre-wrap">{chat.answer}</p>
            {chat.citations.length ? (
              <ul className="mt-4 grid gap-2">
                {chat.citations.map((item) => (
                  <li key={item.node_id} className="panel">
                    <strong>{item.title}</strong>
                    <p>{a11y.language === "legal" ? item.legal_basis : item.plain_language}</p>
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        ) : null}
        {chat.error ? (
          <p className="alert mt-4" role="alert">
            {chat.error}
          </p>
        ) : null}
        {chat.loading ? <p className="mt-4">Czekam na odpowiedź…</p> : null}
      </div>
      <form className="mt-6 grid gap-4" onSubmit={onAsk}>
        <label className="grid gap-2">
          Nie wiem, pomóż mi wybrać
          <textarea
            className="control"
            rows={3}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
          />
        </label>
        <button type="submit" className="btn-primary control" disabled={chat.loading}>
          Dalej
        </button>
      </form>
      <button type="button" className="control mt-4" onClick={() => void chat.start()}>
        Zacznij od nowa
      </button>
    </AppShell>
  );
}
