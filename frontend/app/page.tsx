"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useGuide } from "@/components/GuideProvider";
import { useGuidedChat } from "@/hooks/useGuidedChat";
import { COPY } from "@/lib/copy";

export default function HomePage() {
  const { a11y } = useGuide();
  const chat = useGuidedChat();
  const [message, setMessage] = useState("");
  const liveRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    liveRef.current?.scrollTo({ top: liveRef.current.scrollHeight, behavior: "smooth" });
  }, [chat.lines, chat.loading]);

  function onAsk(event: FormEvent) {
    event.preventDefault();
    const text = message.trim();
    if (!text) return;
    void chat.send({ message: text });
    setMessage("");
  }

  return (
    <AppShell>
      {a11y.hardSituation ? null : <p className="badge">{COPY.badge}</p>}
      <h1 className="hero mt-4">
        {a11y.hardSituation ? (
          COPY.hardHero
        ) : (
          <>
            {COPY.heroTitle} <span className="accent">{COPY.heroAccent}</span>
          </>
        )}
      </h1>
      <p className="mt-4 max-w-2xl">{a11y.hardSituation ? COPY.hardLead : COPY.heroLead}</p>

      <div className="chat-log mt-6" ref={liveRef} aria-live="polite">
        {chat.lines.map((line, index) => (
          <article key={`${line.role}-${index}`} className={`bubble ${line.role}`}>
            <p className="eyebrow">{line.role === "user" ? "Ty" : "Przewodnik"}</p>
            <p className="whitespace-pre-wrap">{line.text}</p>
            {line.citations?.length ? (
              <ul className="mt-3 grid gap-2">
                {line.citations.map((item) => (
                  <li key={item.node_id}>
                    <strong>{item.title}</strong>
                    <span className="block text-sm">
                      {a11y.language === "legal" ? item.legal_basis : item.plain_language}
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        ))}
        {chat.loading ? <p>Chwila, sprawdzam przepisy…</p> : null}
        {chat.error ? (
          <p className="alert" role="alert">
            {chat.error}
          </p>
        ) : null}
      </div>

      {chat.buttons.length ? (
        <div className="mt-4 flex flex-wrap gap-3" role="group" aria-label="Tematy">
          {chat.buttons.map((button) => (
            <button
              key={button.id}
              type="button"
              className="control"
              disabled={chat.loading}
              onClick={() => void chat.send({ button_id: button.id, label: button.label })}
            >
              {button.label}
            </button>
          ))}
        </div>
      ) : null}

      <form className="chat-form mt-6" onSubmit={onAsk}>
        <label className="grid gap-2">
          Napisz, co się dzieje
          <textarea
            className="control"
            rows={3}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Np. jestem w 7. miesiącu ciąży, pracuję na etacie i nie wiem, od czego zacząć."
          />
        </label>
        <div className="mt-4 flex flex-wrap gap-3">
          <button type="submit" className="btn-primary control" disabled={chat.loading}>
            Wyślij
          </button>
          <button type="button" className="control" onClick={() => void chat.start()}>
            Nowa rozmowa
          </button>
        </div>
      </form>
    </AppShell>
  );
}
