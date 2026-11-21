# Backend — silnik zasiłkowy

Deterministyczny silnik (bez LLM) + graf wiedzy NetworkX. Liczby z `app/data/params.json` (stan: listopad 2026).

## Uruchomienie

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Dokumentacja OpenAPI: http://127.0.0.1:8000/docs

## Endpointy

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| POST | `/api/calculate` | Urlopy, stawki 100% / 70% / 81,5%, płatnik, dokumenty, ryzyka |
| POST | `/api/pdf/calculate` | Upload PDF (ZAM, Z-3, poświadczenie ubezpieczenia) → weryfikacja + kalkulacja |
| POST | `/api/chat` | Krok z przyciskami albo pytanie otwarte (GraphRAG + `legal_basis`) |
| GET | `/api/graph` | Wszystkie węzły i krawędzie (mapa) |
| GET | `/api/graph/explain` | Sąsiedztwo węzła i ścieżka „Skąd ten wynik?” |
| POST | `/api/graph/explain` | To samo (body: `node_id`, opcjonalnie `target_id`, `depth`) |
| GET | `/api/admin/params` | Stawki i limity |
| PUT | `/api/admin/params` | Zapis stawek i limitów do `app/data/params.json` |

LLM (opcjonalnie): `OPENAI_API_KEY` albo `LLM_API_KEY`. Bez klucza parser i czat działają na regex + grafie. LLM nie liczy kwot.

## Testy

```bash
cd backend
pytest
```
