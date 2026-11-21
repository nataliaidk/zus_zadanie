from datetime import date, timedelta

from app.models.schemas import ParentProfile


def simulate(kind: str, profile: ParentProfile | None) -> dict:
    today = date(2026, 11, 21)
    banner = "SYMULACJA — to nie jest prawdziwy ZUS, mObywatel ani PUE."
    if kind == "mobywatel":
        return {
            "banner": banner,
            "channel": "mObywatel",
            "logged_in": True,
            "person": "Anna Nowak (symulacja)",
            "pesel_mask": "******1234",
        }
    if kind == "insurance":
        form = profile.employment_form.value if profile else "umowa_o_prace"
        return {
            "banner": banner,
            "title": "Dane z konta ubezpieczonego (symulacja)",
            "insured": True if not profile else profile.insured,
            "title_code": form,
            "since": "2025-01-15",
            "waiting_days": 30 if form == "umowa_o_prace" else 90,
        }
    if kind == "arrears":
        arrears = bool(profile and profile.b2b_arrears)
        return {
            "banner": banner,
            "title": "Zaświadczenie o stanie zadłużenia składek (JDG)",
            "as_of": str(today),
            "amount_pln": 2140.50 if arrears else 0,
            "blocks_benefit": arrears,
        }
    if kind == "ezla":
        return {
            "banner": banner,
            "title": "e-ZLA (symulacja)",
            "code": "B",
            "from": str(today - timedelta(days=12)),
            "to": str(today + timedelta(days=5)),
            "sent_to": ["ZUS", "PUE pracodawcy"],
        }
    if kind == "pue":
        return {
            "banner": banner,
            "title": "PUE / eZUS",
            "inbox": ["Wezwanie do uzupełnienia ZAM (symulacja)", "Potwierdzenie e-ZLA"],
            "ask": "Możesz zapytać konsultanta PUE — to tylko podgląd.",
        }
    if kind == "application":
        payer = "pracodawca" if profile and profile.company_insured_above_20 else "ZUS"
        return {
            "banner": banner,
            "title": "Wniosek o urlop i zasiłek (ZAM)",
            "form": "ZAM",
            "replaces": ["ZUR", "ZAO", "Z-3b"],
            "sent_to": payer,
            "status": "wysłano (symulacja)",
            "zus_pl": "https://www.zus.pl",
        }
    if kind == "rsc":
        return {
            "banner": banner,
            "title": "Wniosek o odpis aktu urodzenia (RSC)",
            "url": "https://www.gov.pl/web/cyfryzacja/rejestr-stanu-cywilnego",
            "status": "złożono wniosek o odpis skrócony (symulacja)",
        }
    raise KeyError(kind)
