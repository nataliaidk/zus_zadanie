"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { loadParams, saveParams } from "@/lib/api";

export default function AdminPage() {
  const [text, setText] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    void loadParams()
      .then((body) => setText(JSON.stringify(body, null, 2)))
      .catch((err: unknown) => {
        setStatus(err instanceof Error ? err.message : "Nie wczytano params.json");
      });
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      const payload = JSON.parse(text) as Record<string, unknown>;
      const saved = await saveParams(payload);
      setText(JSON.stringify(saved, null, 2));
      setStatus("Zapisano.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Zapis nieudany.");
    }
  }

  return (
    <AppShell>
      <h1 className="font-semibold">Panel parametrów</h1>
      <p className="mt-2">
        GET/PUT /api/admin/params. Tu zmieniasz stawki i limity bez ruszania kodu silnika.
      </p>
      <form className="mt-4 grid gap-4" onSubmit={onSubmit}>
        <label className="grid gap-2">
          params.json
          <textarea
            className="border p-2 font-mono"
            rows={24}
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </label>
        <button type="submit" className="border px-4 py-2">
          Zapisz
        </button>
      </form>
      <p className="mt-4" aria-live="polite">
        {status}
      </p>
    </AppShell>
  );
}
