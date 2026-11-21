"""Minimal text PDFs for parser tests (Helvetica, ASCII labels)."""


def make_pdf(lines: list[str]) -> bytes:
    content_ops = ["BT", "/F1 12 Tf"]
    y = 740
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_ops.append(f"50 {y} Td ({safe}) Tj")
        content_ops.append("0 -16 Td")
        y -= 16
    content_ops.append("ET")
    stream = "\n".join(content_ops).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.1\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, xref_pos)
    )
    return bytes(out)


ZAM_LINES = [
    "WNIOSEK ZAM",
    "Wniosek o zasilek macierzynski",
    "Data porodu: 01.11.2026",
    "Data zlozenia wniosku: 10.11.2026",
    "Liczba dzieci urodzonych przy jednym porodzie: 1",
    "Tytul ubezpieczenia: umowa o prace",
    "Wymiar czasu pracy: pelny etat",
    "Zaswiadczenie Za zyciem: nie",
    "Wczesniak: nie",
]

Z3_LINES = [
    "Zaswiadczenie platnika skladek Z-3",
    "Liczba ubezpieczonych na dzien 30 listopada poprzedniego roku: 12",
    "Rodzaj umowy: umowa o prace",
    "Wymiar czasu pracy: 1/2 etatu",
    "Data porodu: 01.11.2026",
    "Liczba dzieci: 2",
    "Podleganie od: 01.01.2026",
]

INSURANCE_LINES = [
    "Poswiadczenie ubezpieczenia chorobowego",
    "Tytul: umowa o prace",
    "Podleganie od: 01.01.2026",
    "Na dzien porodu: podlega ubezpieczeniu chorobowemu",
    "Zaleglosci skladek: nie",
    "Data porodu: 01.11.2026",
    "Liczba dzieci: 1",
    "Liczba ubezpieczonych: 8",
]

ZUR_LINES = [
    "WNIOSEK ZUR",
    "Wniosek o zasilek macierzynski za okres urlopu rodzicielskiego",
    "Data porodu: 01.11.2026",
    "Liczba dzieci: 1",
    "umowa o prace",
]
