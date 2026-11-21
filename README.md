# Zasiłkowy Przewodnik Przyszłego Rodzica

Aplikacja na hackathon ZUS (HackNation). Stan prawny: **listopad 2026**. To **nie jest prawdziwy ZUS** — logowanie i wnioski są **symulacją**.

**Repozytorium:** https://github.com/nataliaidk/zus_zadanie

## Uruchomienie dla jurora (lokalnie)

Jedno polecenie z katalogu repo:

```bash
./start.sh
```

Otwórz **http://127.0.0.1:8000**

- Jeśli jest Docker: `docker compose up --build` (to samo, port 8000).
- Bez Dockera: skrypt sam stawia venv, buduje UI i serwuje API + stronę razem.

Logowanie (demonstracja): PUE `anna.nowak` / `HasloAnna1` albo mObywatel w nagłówku. Juror PDF: **/juror**.

## Wdrożenie publiczne (Vercel)

Vercel = tylko frontend. API (Python) na Render/Fly z `Dockerfile`. Krok po kroku: [docs/wdrozenie-vercel.md](docs/wdrozenie-vercel.md).

## Materiały §4

- Opis i AI: [docs/opis-projektu.md](docs/opis-projektu.md)
- 10 slajdów: [docs/index.html](docs/index.html), [docs/prezentacja.pdf](docs/prezentacja.pdf)
- Film 3 min: [docs/demo-3min.mp4](docs/demo-3min.mp4)
- Zrzuty: [docs/screens/](docs/screens/)

## Rozwój (dwa procesy)

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd frontend && npm install && npm run dev
```

Wtedy UI jest na http://127.0.0.1:3000 (proxy `/api` → 8000).

Testy: `cd backend && pytest`
