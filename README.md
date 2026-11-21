# Zasiłkowy Przewodnik Przyszłego Rodzica

Aplikacja na hackathon ZUS (HackNation). Dostępność WCAG 2.1/2.2 AA+ i dostępność poznawcza oraz dokładność prawna (stan na listopad 2026).

Repozytorium: [github.com/nataliaidk/zus_zadanie](https://github.com/nataliaidk/zus_zadanie)

## Stack

- Frontend: Next.js App Router, TypeScript, Tailwind (układ + stany `:focus-visible`)
- Backend: Python 3.11+, FastAPI, Pydantic, NetworkX
- API: REST JSON (`/api` z frontu jest proxowane do FastAPI)

## Uruchomienie

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Otwórz http://127.0.0.1:3000 — belka profili: Niezalogowany / Anna etat / Piotr B2B / Kasia zlecenie.

Strony: Start (czat), Kalkulator, Plan, Ciąża, Dokumenty, Usługi (symulacje), Wsparcie, Ryzyka, Przepisy, Juror (PDF), Admin.

Testy silnika: `cd backend && pytest`

## Agent files

- `.cursorrules` — produkt, prawo (listopad 2026), UX wireframe-first
- `AGENTS.md` i `.cursor/rules/ponytail.mdc` — Ponytail (rule-file install, bez hooków `~/.cursor`)
- `.cursor/rules/ux-wireframe-first.mdc` — bez dekoracyjnego UI; hooki `useParentPlan`, `useGuidedChat`
- Źródła prawne: [docs/zrodla](docs/zrodla)
