"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DecisionCard } from "@/components/DecisionCard";
import { useGuide } from "@/components/GuideProvider";
import { useGuidedChat } from "@/hooks/useGuidedChat";

export default function HomePage() {
  const { applyResult, a11y } = useGuide();
  const chat = useGuidedChat(applyResult);
  const [message, setMessage] = useState("");

  function onAsk(event: FormEvent) {
    event.preventDefault();
    void chat.ask(message);
    setMessage("");
  }

  return (
    <AppShell aside={<DecisionCard />}>
      <h1 className="font-semibold">Porozmawiajmy o Twoim urlopie</h1>
      <p className="mt-2">Jedna decyzja na raz. Wybierz odpowiedź albo zadaj pytanie.</p>

      {chat.question ? (
        <div className="mt-4">
          <h2 className="font-semibold">{chat.question}</h2>
          {chat.helper ? <p className="mt-2">{chat.helper}</p> : null}
        </div>
      ) : null}

      {chat.buttons.length ? (
        <div className="mt-4 grid gap-4" role="group" aria-label="Gotowe odpowiedzi">
          {chat.buttons.map((button) => (
            <button
              key={button.id}
              type="button"
              className="border px-4 py-2 text-left"
              disabled={chat.loading}
              onClick={() => void chat.answerButton(button.id)}
            >
              {button.label}
            </button>
          ))}
        </div>
      ) : null}

      <div aria-live="polite">
        {chat.answer ? (
          <article className="mt-4 border p-4">
            <p className="whitespace-pre-wrap">{chat.answer}</p>
            {chat.citations.length ? (
              <ul className="mt-4 grid gap-2">
                {chat.citations.map((item) => (
                  <li key={item.node_id} className="border p-2">
                    <strong>{item.title}</strong>
                    <p>{a11y.language === "legal" ? item.legal_basis : item.plain_language}</p>
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        ) : null}
        {chat.error ? <p className="mt-4">{chat.error}</p> : null}
        {chat.loading ? <p className="mt-4">Czekam na odpowiedź…</p> : null}
      </div>

      <form className="mt-4 grid gap-4" onSubmit={onAsk}>
        <label className="grid gap-2">
          Twoje pytanie
          <textarea
            className="border p-2"
            rows={4}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
          />
        </label>
        <button type="submit" className="border px-4 py-2" disabled={chat.loading}>
          Zapytaj
        </button>
      </form>

      <button type="button" className="mt-4 border px-4 py-2" onClick={() => void chat.start()}>
        Zacznij od nowa
      </button>
    </AppShell>
  );
}
