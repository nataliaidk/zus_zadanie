from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import AdminParams, ChatRequest, ExplainRequest, ParentProfile
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService
from app.services.params_service import ParamsService
from app.services.pdf_parser import parse_and_calculate
from app.services.rule_engine import calculate

app = FastAPI(
    title="Zasiłkowy Przewodnik Przyszłego Rodzica",
    description=(
        "Deterministyczny silnik zasiłkowy i graf wiedzy (stan prawny: listopad 2026). "
        "LLM tylko do parsowania PDF i brzmienia odpowiedzi z podgrafu — nigdy do kwot."
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
    return parse_and_calculate(data, params_service.get())


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
