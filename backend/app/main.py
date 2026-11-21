import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.models.schemas import AdminParams, ChatRequest, ExplainRequest, ParentProfile
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService
from app.services.params_service import ParamsService
from app.services.pdf_parser import parse_and_calculate
from app.services.rule_engine import calculate
from app.services.samples import calculate_sample, list_samples, sample_pdf
from app.services.sim_service import simulate

app = FastAPI(
    title="Zasiłkowy Przewodnik Przyszłego Rodzica",
    description=(
        "Urlopy i zasiłki dla rodziców (stan prawny: listopad 2026). "
        "Kwoty liczy kod, nie model językowy."
    ),
    version="0.3.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
params_service = ParamsService()
graph_service = GraphService()
chat_service = ChatService(graph_service, params_service.get())

MAX_PDF_BYTES = 10 * 1024 * 1024


@app.post("/api/calculate")
def api_calculate(profile: ParentProfile):
    return calculate(profile, params_service.get())


@app.get("/api/graph")
def api_graph():
    return graph_service.dump()


@app.get("/api/graph/explain")
def api_graph_explain_get(
    node_id: str = Query(..., description="Węzeł, którego wynik wyjaśniamy"),
    target_id: str | None = Query(None, description="Opcjonalny drugi koniec ścieżki"),
    depth: int = Query(2, ge=1, le=6),
):
    try:
        return graph_service.explain(node_id, target_id, depth)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Nieznany węzeł: {exc}") from exc


@app.post("/api/graph/explain")
def api_graph_explain_post(body: ExplainRequest):
    try:
        return graph_service.explain(body.node_id, body.target_id, body.depth)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Nieznany węzeł: {exc}") from exc


@app.post("/api/pdf/calculate")
async def api_pdf_calculate(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Wgraj plik PDF (ZAM, Z-3 albo poświadczenie ubezpieczenia).")
    data = await file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF jest za duży (maks. 10 MB).")
    if not data:
        raise HTTPException(status_code=400, detail="Pusty plik.")
    return parse_and_calculate(data, params_service.get(), source_name=file.filename)


@app.post("/api/chat")
def api_chat(body: ChatRequest):
    chat_service.params = params_service.get()
    return chat_service.handle(body)


@app.get("/api/admin/params")
def api_get_params():
    return params_service.get()


@app.put("/api/admin/params")
def api_put_params(payload: AdminParams):
    return params_service.replace(payload.model_dump(mode="json"))


@app.get("/api/charities")
def api_charities():
    path = Path(__file__).resolve().parent / "data" / "charities.json"
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/samples")
def api_samples():
    return list_samples()


@app.get("/api/samples/{sample_id}/pdf")
def api_sample_pdf(sample_id: str):
    try:
        _meta, pdf = sample_pdf(sample_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Nieznana sprawa testowa.") from exc
    return Response(content=pdf, media_type="application/pdf")


@app.post("/api/samples/{sample_id}/calculate")
def api_sample_calculate(sample_id: str):
    try:
        return calculate_sample(sample_id, params_service.get())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Nieznana sprawa testowa.") from exc


@app.post("/api/sim/{kind}")
async def api_sim(kind: str, request: Request):
    raw = await request.body()
    profile = None
    if raw.strip():
        try:
            profile = ParentProfile.model_validate_json(raw)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Niepoprawny profil.") from exc
    try:
        return simulate(kind, profile)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Nieznana symulacja.") from exc


def _frontend_out() -> Path:
    return Path(__file__).resolve().parents[2] / "frontend" / "out"


@app.get("/api/health")
def api_health():
    return {"ok": True, "ui": _frontend_out().is_dir()}


_ui = _frontend_out()
if _ui.is_dir():
    app.mount("/", StaticFiles(directory=_ui, html=True), name="ui")
