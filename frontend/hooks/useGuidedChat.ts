"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { chat } from "@/lib/api";
import type { CalculationResult, ChatButton, ChatCitation, ParentProfile } from "@/lib/types";

export function useGuidedChat(onResult?: (profile: ParentProfile, result: CalculationResult) => void) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<string | null>(null);
  const [helper, setHelper] = useState<string | null>(null);
  const [buttons, setButtons] = useState<ChatButton[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<ChatCitation[]>([]);
  const [complete, setComplete] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  const apply = useCallback(
    (body: Awaited<ReturnType<typeof chat>>) => {
      setSessionId(body.session_id);
      setQuestion(body.question);
      setHelper(body.helper);
      setButtons(body.buttons ?? []);
      setAnswer(body.answer);
      setCitations(body.citations ?? []);
      setComplete(body.complete);
      if (body.complete && body.calculation && body.profile) {
        onResult?.(body.profile as ParentProfile, body.calculation);
      }
    },
    [onResult],
  );

  const start = useCallback(async () => {
    setLoading(true);
    setError(null);
    setComplete(false);
    setAnswer(null);
    setCitations([]);
    try {
      apply(await chat({ action: "start" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Czat nie działa.");
    } finally {
      setLoading(false);
    }
  }, [apply]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void start();
  }, [start]);

  const answerButton = useCallback(
    async (buttonId: string) => {
      if (!sessionId) return;
      setLoading(true);
      setError(null);
      try {
        apply(await chat({ session_id: sessionId, action: "answer", button_id: buttonId }));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Nie udało się zapisać odpowiedzi.");
      } finally {
        setLoading(false);
      }
    },
    [apply, sessionId],
  );

  const ask = useCallback(
    async (message: string) => {
      if (!sessionId || !message.trim()) return;
      setLoading(true);
      setError(null);
      try {
        apply(
          await chat({
            session_id: sessionId,
            action: question && !buttons.length ? "answer" : "question",
            message: message.trim(),
          }),
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Nie udało się zadać pytania.");
      } finally {
        setLoading(false);
      }
    },
    [apply, buttons.length, question, sessionId],
  );

  return {
    question,
    helper,
    buttons,
    answer,
    citations,
    complete,
    loading,
    error,
    start,
    answerButton,
    ask,
  };
}
