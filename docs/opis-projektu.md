# Zasiłkowy Przewodnik Przyszłego Rodzica

**Hackathon ZUS / HackNation · stan prawny: listopad 2026**

Aplikacja webowa, która prowadzi przyszłego rodzica (i drugiego rodzica) przez urlopy i zasiłki: co przysługuje, ile to jest w złotych, jakie dokumenty złożyć i gdzie — pracodawca albo ZUS. Język prosty. Kwoty nigdy nie pochodzą z modelu językowego.

To **nie jest prawdziwy ZUS**. Logowanie mObywatel, PUE/eZUS, e-ZLA i wysyłka wniosków są wyłącznie **symulacją** (baner SYMULACJA).

Repozytorium: https://github.com/nataliaidk/zus_zadanie

## Problem

Rodzic stoi przed ustawą zasiłkową, Kodeksem pracy i zmianą z 24 października 2026 r. (jeden wniosek **ZAM** zamiast ZUR, ZAO i Z-3b). Łatwo pomylić płatnika, stawkę 81,5% (21 dni), 14 tygodni tylko dla matki i 9 tygodni nieprzenoszalnych.

## Co aplikacja robi

- Czat z jedną decyzją na krok i kartą planu (wymiar + kwota).
- Zintegrowany kalkulator: poród, adopcja, rodzina zastępcza niezawodowa, liczba i wiek dzieci, Za życiem, łączenie urlopu z pracą, oboje rodzice naraz, indywidualna podstawa wymiaru.
- Ciąża: zasiłek chorobowy kod B, świadczenie rehabilitacyjne, macierzyński po utracie pracy, brak uprawnień.
- Dokumenty i terminy: ZAM, Z-3 / Z-3a, pracodawca (>20 ubezpieczonych) albo ZUS.
- Radar ryzyk utraty albo zmiany świadczenia.
- Fundacje przy stracie, wcześniaku, poronieniu, ciężko chorym dziecku.
- Tryb jurora: wybór sprawy testowej albo wgranie PDF.
- Panel admina: stawki i maksima bez zmiany kodu silnika.
- Dostępność: klawiatura, 44×44 px, `aria-live`, kontrast, czcionka 100/125/150%, tryb „Trudna sytuacja”.

## Gdzie jest AI, a gdzie nie

| Zadanie | Kto liczy |
|---|---|
| Wymiar urlopu, stawka %, kwota w zł, terminy, blokady (poka-yoke) | **Python** — `backend/app/services/rule_engine.py` + `params.json` |
| Odczyt pól z PDF (daty, forma zatrudnienia, liczba dzieci, podstawa) | **Regex zawsze**; LLM tylko gdy jest klucz API i regex nie wystarcza |
| Empatyczna odpowiedź w czacie | LLM **wyłącznie** na podgrafie wiedzy (GraphRAG). Nie wolno mu podawać kwot ani długości urlopu z głowy |
| Graf wiedzy | `knowledge_graph.json` + NetworkX — bez modelu |

**Zasada konkursowa:** halucynacja przy pieniądzach jest niedopuszczalna. Dlatego silnik jest deterministyczny. Juror może to sprawdzić: ta sama sprawa PDF zawsze daje ten sam wynik.

## Jak testować (juror)

1. Uruchom backend i frontend (README) albo otwórz demo, jeśli jest publiczny URL.
2. Profil **Anna** — 20 tyg. macierzyńskiego i kwota z podstawy 5200 zł.
3. **Juror** — lista spraw (`GET /api/samples`) albo wgranie PDF. Gotowe PDF: `GET /api/samples/{id}/pdf` (np. `zam-etat`, `z3-mniejszy`, `zur-zniesiony`).
4. Kalkulator: adopcja / Za życiem / ½ etatu.
5. Usługi: każdy przycisk ma baner **SYMULACJA**.
