from tests.pdf_fixtures import INSURANCE_LINES, Z3_LINES, ZAM_LINES, ZUR_LINES, make_pdf


def pdf_for_kind(kind: str, base: float | None) -> bytes:
    extra = [f"Podstawa wymiaru: {base:.2f} PLN"] if base else []
    if kind == "z3":
        lines = Z3_LINES + extra
    elif kind == "insurance":
        lines = INSURANCE_LINES + extra
    elif kind == "zur":
        lines = ZUR_LINES + extra
    else:
        lines = ZAM_LINES + extra
    return make_pdf(lines)
