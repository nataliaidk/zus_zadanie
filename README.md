# Zasiłkowy Przewodnik Przyszłego Rodzica

Aplikacja na hackathon ZUS (HackNation). Dostępność WCAG 2.1/2.2 AA+ i dokładność prawna (stan na **listopad 2026**). To **nie jest prawdziwy ZUS** — logowanie i wnioski są wyłącznie **symulacją**.

- **Repozytorium:** https://github.com/nataliaidk/zus_zadanie
- **Pull request:** https://github.com/nataliaidk/zus_zadanie/pull/1
- **Opis projektu i gdzie jest AI:** [docs/opis-projektu.md](docs/opis-projektu.md)
- **Prezentacja (10 slajdów, HTML):** [docs/index.html](docs/index.html)
- **Prezentacja (PDF):** [docs/prezentacja.pdf](docs/prezentacja.pdf)
- **Film ≤ 3 min:** [docs/demo-3min.mp4](docs/demo-3min.mp4)
- **Zrzuty:** [docs/screens/](docs/screens/)
- **Demo na żywo (aplikacja):** brak publicznego hostingu bez sekretów (Vercel/Render) — odpal lokalnie, patrz niżej.
- **Demo materiałów:** po włączeniu GitHub Pages z katalogu `docs/` — `https://nataliaidk.github.io/zus_zadanie/` (prezentacja + film + zrzuty).

## Sprawy PDF dla jurora

Strona **[/juror](http://127.0.0.1:3000/juror)** — wybór gotowej sprawy albo upload własnego PDF.

| Co | Gdzie |
|----|--------|
| Lista spraw | `GET /api/samples` |
| PDF sprawy | `GET /api/samples/{id}/pdf` |
| Identyfikatory | `zam-etat`, `z3-mniejszy`, `ubezp-ok`, `zur-zniesiony`, `ciaza-kod-b`, `brak-uprawnien`, `za-zyciem`, `adopcja`, `zastepcza`, `pol-etatu-razem` |
| Metadane | `backend/app/data/samples.json` |

## Stack

- Frontend: Next.js App Router, TypeScript, Tailwind
- Backend: Python 3.11+, FastAPI, Pydantic, NetworkX
- Kwoty: silnik Python (`rule_engine.py`). LLM tylko do pól PDF i brzmienia czatu.

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

Otwórz http://127.0.0.1:3000 — belka: Niezalogowany / Anna etat / Piotr B2B / Kasia zlecenie.

Strony: Start, Kalkulator, Plan, Ciąża, Dokumenty, Usługi (SYMULACJA), Wsparcie, Ryzyka, Przepisy, Juror, Admin.

Testy silnika: `cd backend && pytest`

## Źródła

[docs/zrodla](docs/zrodla) — brief, ustawa zasiłkowa, Kodeks pracy, poradnik ZUS 2026.
