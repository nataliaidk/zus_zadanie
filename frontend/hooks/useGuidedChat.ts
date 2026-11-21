"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { chat } from "@/lib/api";
import type { ChatButton, ChatCitation } from "@/lib/types";

export type ChatLine = {
  role: "user" | "assistant";
  text: string;
  citations?: ChatCitation[];
};

export function useGuidedChat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [buttons, setButtons] = useState<ChatButton[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  const start = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const body = await chat({ action: "start" });
      setSessionId(body.session_id);
      setButtons(body.buttons ?? []);
      setLines(body.answer ? [{ role: "assistant", text: body.answer, citations: body.citations }] : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Czat nie działa.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void start();
  }, [start]);

  const send = useCallback(
    async (opts: { message?: string; button_id?: string; label?: string }) => {
      if (!sessionId) return;
      const userText = opts.label ?? opts.message ?? "";
      if (userText) {
        setLines((prev) => [...prev, { role: "user", text: userText }]);
      }
      setLoading(true);
      setError(null);
      try {
        const body = await chat({
          session_id: sessionId,
          action: opts.button_id && !opts.message ? "answer" : "question",
          button_id: opts.button_id,
          message: opts.message,
        });
        setButtons(body.buttons ?? []);
        if (body.answer) {
          setLines((prev) => [
            ...prev,
            { role: "assistant", text: body.answer as string, citations: body.citations },
          ]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Nie udało się wysłać wiadomości.");
      } finally {
        setLoading(false);
      }
    },
    [sessionId],
  );

  return { lines, buttons, loading, error, start, send };
}
