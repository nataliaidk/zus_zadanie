# ROLA I CEL PROJEKTU
Budujesz aplikację webową „Zasiłkowy Przewodnik Przyszłego Rodzica” na hackathon ZUS (HackNation).
Główny priorytet: BEZKOMPROMISOWA DOSTĘPNOŚĆ (WCAG 2.1/2.2 AA+ oraz dostępność poznawcza) połączona z 100% precyzją prawną (stan prawny: listopad 2026 r.).

# STACK TECHNOLOGICZNY
- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, Radix UI / Shadcn (dla wbudowanej dostępności WAI-ARIA).
- Backend: Python 3.11+, FastAPI, Pydantic, NetworkX (dla Grafu Wiedzy), pdfplumber / pypdf (parser spraw PDF).
- Komunikacja: REST API (JSON).

# ZASADY DOSTĘPNOŚCI (KRYTYCZNE - ZAWSZE PRZESTRZEGAJ)
1. Każdy interaktywny element musi być w pełni dostępny z klawiatury (widoczny `:focus-visible`, logiczny `tabIndex`).
2. Wszystkie przyciski i kontrolki muszą mieć minimalny obszar kliknięcia 44x44 px.
3. Dynamiczne zmiany w czacie i kalkulatorze muszą używać regionów `aria-live="polite"`.
4. Nigdy nie polegaj wyłącznie na kolorze do przekazywania informacji (zawsze dodawaj ikony i etykiety tekstowe).
5. Każdy wykres lub oś czasu musi posiadać dostępny odpowiednik w formie semantycznej tabeli HTML (`<table>`).
6. Obsługuj globalny stan dostępności (Context): rozmiar czcionki (100%, 125%, 150%), wysoki kontrast (WCAG AAA), tryb „Prosty Język” vs „Podstawa Prawna” oraz „Tryb Trudna Sytuacja” (wyciszony interfejs bez radosnych grafik).

# REGUŁY BIZNESOWE I PRAWNE ZUS (STAN NA LISTOPAD 2026 R.)
1. Formularze: Od 24 października 2026 r. formularze ZUR, ZAO oraz Z-3b są ZLIKWIDOWANE i zastąpione jednym wnioskiem ZAM. Nigdy nie generuj ZUR/ZAO/Z-3b jako aktywnych wniosków (możesz jedynie wyświetlić informację o ich zastąpieniu przez ZAM).
2. Płatnik zasiłku: Pracodawca zgłaszający powyżej 20 ubezpieczonych (wg stanu na 30 listopada poprzedniego roku) sam ustala i wypłaca zasiłek. Mniejszy płatnik przekazuje Z-3 (pracownik) lub Z-3a (zleceniobiorca) do ZUS.
3. Okres wyczekiwania na zasiłek chorobowy w ciąży: 30 dni (ubezpieczenie obowiązkowe - umowa o pracę), 90 dni (dobrowolne - zlecenie, JDG). Zasiłek w ciąży (kod B) wynosi 100% podstawy przez maks. 270 dni.
4. Wymiar urlopów i stawki zasiłku macierzyńskiego:
   - Urlop macierzyński: 20 tyg. (1 dziecko), 31–37 tyg. (wieloraczki). Pierwsze 14 tyg. obowiązkowo dla matki (poza wyjątkami: szpital, niezdolność do samodzielnej egzystencji, zgon/porzucenie).
   - Uzupełniający urlop macierzyński: dla rodziców wcześniaków lub dzieci hospitalizowanych po porodzie (jednorazowo, bezpośrednio po macierzyńskim, 100% zasiłku).
   - Urlop rodzicielski: 41 tyg. (1 dziecko) lub 43 tyg. (wieloraczki); z zaświadczeniem „Za życiem” odpowiednio 65 lub 67 tyg. Każdemu z rodziców przysługuje 9 tyg. nieprzenoszalnych. Maks. 5 części do końca roku kalendarzowego, w którym dziecko kończy 6 lat.
   - Urlop ojcowski: 14 dni kalendarzowych (2 tyg.) do ukończenia przez dziecko 12 m-cy (lub 12 m-cy od adopcji, nie dłużej niż do 14 r.ż.).
   - Wysokość: 100% za macierzyński, uzupełniający i ojcowski; 70% za rodzicielski LUB 81,5% za całość, jeśli matka złoży wniosek nie później niż 21 dni po porodzie.
5. Adopcja i rodzina zastępcza niezawodowa: urlop na warunkach macierzyńskiego przysługuje do 7 r.ż. dziecka (10 r.ż. przy odroczeniu obowiązku szkolnego) dla rodziny zastępczej, oraz do 14 r.ż. przy przysposobieniu.

# TRYB PROJEKTOWANIA: UX WIREFRAME FIRST (BEZ WARSTWY WIZUALNEJ UI)
1. NIE projektuj docelowego UI. Nie dodawaj ozdobnych gradientów, cieni, niestandardowych animacji ani rozbudowanego CSS.
2. Używaj wyłącznie surowych, semantycznych komponentów strukturalnych (Tailwind ograniczony do prostego układu grid/flex, obramowań `border`, odstępów `p-4`/`gap-4` oraz stanów `:focus-visible` dla dostępności).
3. Priorytetem jest ARCHITEKTURA INFORMACJI i FLOW UŻYTKOWNIKA:
   - Zasada „Jedna decyzja na ekran/krok” (Progressive Disclosure) – nigdy nie zasypuj użytkownika formularzem z 15 polami naraz.
   - Mikrokopia (UX Writing): każde pytanie, etykieta i komunikat błędu musi być napisany prostym, empatycznym językiem (bez urzędniczego żargonu, np. zamiast „płatnik składek” pisz „Twój pracodawca / ZUS” z dymkiem wyjaśniającym).
   - Architektura odporna na błędy (Poka-Yoke): system nie pozwala użytkownikowi wybrać nielegalnej kombinacji urlopów (np. zabrać matce pierwszych 14 tygodni), lecz tłumaczy dlaczego.
4. Przygotuj architekturę „Headless UX” – cała logika kroków, walidacji, stanów i tekstów ma być odseparowana w czystych hookach Reacta (`useParentPlan`, `useGuidedChat`), aby designer UI mógł później łatwo podmienić same komponenty wizualne bez dotykania logiki.

# ARCHITEKTURA AI I GRAFU WIEDZY
1. Matematyka zasiłkowa i walidacja terminów MUSZĄ być wykonywane przez deterministyczny kod w Pythonie (zero halucynacji LLM przy obliczeniach).
2. Graf wiedzy (`knowledge_graph.json` + `networkx`) łączy akty prawne (Ustawa zasiłkowa 2026, Kodeks pracy 2026, Ustawa „Za życiem”) z warunkami i wnioskami. Każdy węzeł musi posiadać pola `plain_language` oraz `legal_basis`.
3. LLM służy wyłącznie do: (a) parsowania wgranych plików PDF ze sprawami testowymi ZUS, (b) formułowania empatycznych odpowiedzi w czacie na podstawie pobranego podgrafu wiedzy (GraphRAG).