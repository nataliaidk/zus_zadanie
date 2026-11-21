"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useGuide } from "@/components/GuideProvider";
import { useGuidedChat, type ChatLine } from "@/hooks/useGuidedChat";
import { COPY } from "@/lib/copy";

function ChatBubble({ line }: { line: ChatLine }) {
  const { a11y } = useGuide();
  const [legalOpen, setLegalOpen] = useState(false);
  const showLegal = a11y.language === "legal" || legalOpen;
  const hasLaw = Boolean(line.citations?.length) && line.role === "assistant";

  return (
    <article className={`bubble ${line.role}`}>
      <p className="eyebrow">{line.role === "user" ? "Ty" : "Przewodnik"}</p>
      <p className="whitespace-pre-wrap">{line.text}</p>
      {hasLaw ? (
        <div className="mt-3 grid gap-2">
          <button
            type="button"
            className="control"
            aria-expanded={showLegal}
            onClick={() => setLegalOpen((open) => !open)}
          >
            Podstawa prawna
          </button>
          {showLegal ? (
            <ul className="grid gap-2">
              {line.citations?.map((item) => (
                <li key={item.node_id}>
                  <strong>{item.title}</strong>
                  <span className="block text-sm">{item.legal_basis}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

export default function HomePage() {
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
      <p className="badge">{COPY.badge}</p>
      <h1 className="hero mt-4">
        {COPY.heroTitle} <span className="accent">{COPY.heroAccent}</span>
      </h1>
      <p className="mt-4 max-w-2xl">{COPY.heroLead}</p>

      <div className="chat-log mt-6" ref={liveRef} aria-live="polite">
        {chat.lines.map((line, index) => (
          <ChatBubble key={`${line.role}-${index}`} line={line} />
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
