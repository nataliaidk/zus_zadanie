# Jak wdrożyć na Vercel (i API)

Vercel serwuje **Next.js**. Silnik zasiłku jest w **Pythonie (FastAPI)** — tego Vercel nie odpalisz w tym projekcie. Najpierw API, potem frontend.

Konto: zaloguj się na [vercel.com](https://vercel.com) przez GitHub (to samo konto co `nataliaidk/zus_zadanie`).

## 1. Backend (Render, darmowy Docker)

Dockerfile w katalogu głównym repo już jest.

1. Wejdź na https://render.com → **New** → **Web Service** → podłącz `nataliaidk/zus_zadanie`.
2. Branch: `main`. Runtime: **Docker**. Port: `8000`.
3. Deploy. Dostaniesz adres, np. `https://zasilkowy.onrender.com`.
4. Sprawdź: `https://….onrender.com/api/health` → `{"ok":true,…}`.

Darmowy Render usypia się — pierwsze otwarcie może trwać ~30 s.

*(Zamiast Render: Railway albo Fly.io, ten sam Dockerfile.)*

## 2. Frontend na Vercel

1. https://vercel.com/new → import **nataliaidk/zus_zadanie**.
2. **Root Directory:** `frontend` (przycisk *Edit*).
3. Framework: Next.js. Build: `next build`. Output: zostaw puste.
4. Environment Variable:
   - Name: `BACKEND_URL`
   - Value: adres z kroku 1 **bez** ukośnika na końcu, np. `https://zasilkowy.onrender.com`
5. **Deploy**.

Vercel proxy’uje `/api/*` do FastAPI (`next.config.ts` → `rewrites`). Juror otwiera adres `*.vercel.app`, wgrywa PDF na **/juror**, kalkulator liczy na backendzie.

## 3. Z terminala (to samo)

```bash
# raz: npx vercel login
cd frontend
BACKEND_URL=https://zasilkowy.onrender.com npx vercel --prod --yes
```

Gdy zapyta o katalog: `frontend`. Potem w dashboardzie dopisz `BACKEND_URL` i zrób Redeploy.

## Czego nie robić

- Nie ustawiaj `NEXT_EXPORT=1` na Vercel — wtedy nie ma proxy `/api`.
- Nie wskazuj Root Directory na cały repo (Next jest w `frontend/`).
- Upload PDF na darmowym Vercel: limit ~4,5 MB (w API jest 10 MB).

## Prościej niż Vercel: jeden adres

Jeśli nie zależy Ci na domenie Vercel, wystarczy sam Render z Dockerfile. Juror otwiera `https://….onrender.com` (UI + API razem, jak `./start.sh` lokalnie).
