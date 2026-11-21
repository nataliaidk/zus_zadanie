# Materiały konkursowe (§4)

| Plik | Co to jest |
|------|------------|
| [opis-projektu.md](opis-projektu.md) | Tytuł, opis, gdzie jest AI |
| [index.html](index.html) | Prezentacja — 10 slajdów (otwórz w przeglądarce) |
| [prezentacja.pdf](prezentacja.pdf) | Te same 10 slajdów jako PDF |
| [screens/](screens/) | Zrzuty desktop + mobile |
| [demo-3min.mp4](demo-3min.mp4) | Film 2 min 59 s — scenariusz z briefu §4 |
| [zrodla/](zrodla/) | Akty i brief ZUS |

## Sprawy PDF dla jurora

- Lista: `GET /api/samples` (albo strona **/juror**)
- Plik: `GET /api/samples/{id}/pdf`
- Identyfikatory: `zam-etat`, `z3-mniejszy`, `ubezp-ok`, `zur-zniesiony`, `ciaza-kod-b`, `brak-uprawnien`, `za-zyciem`, `adopcja`, `zastepcza`, `pol-etatu-razem`
- Źródło metadanych: `backend/app/data/samples.json`
- Własny wniosek: upload na **/juror**
