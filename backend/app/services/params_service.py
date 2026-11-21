import json
from pathlib import Path
from typing import Any

from app.models.schemas import AdminParams

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_PARAMS_PATH = DATA_DIR / "params.json"


class ParamsService:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_PARAMS_PATH
        self._cache: dict[str, Any] | None = None

    def get(self) -> dict[str, Any]:
        if self._cache is None:
            self._cache = json.loads(self.path.read_text(encoding="utf-8"))
        return self._cache

    def replace(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated = AdminParams.model_validate(payload)
        data = validated.model_dump(mode="json")
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._cache = data
        return data
