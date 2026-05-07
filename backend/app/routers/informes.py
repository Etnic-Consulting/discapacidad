"""
L09 + L17 · Endpoints de informes pre-renderizados (5 niveles).

Endpoints:
  GET /api/v1/informes/_index                 lista todos los informes pre-renderizados
  GET /api/v1/informes/{tipo}/{id}            HTML del informe
  GET /api/v1/informes/{tipo}/{id}/data       JSON canónico (datos + metadata fuente)
  GET /api/v1/informes/{tipo}/{id}/pdf        PDF (lazy gen vía WeasyPrint)
  GET /api/v1/informes/{tipo}/{id}/docx       Word (lazy gen vía python-docx)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()

NIVELES_VALIDOS = {"macro", "dpto", "mpio", "pueblo", "resguardo"}

BACKEND_ROOT = Path(__file__).resolve().parents[2]
INFORMES_DIR = BACKEND_ROOT / "_static" / "informes"


def _path_for(tipo: str, id_: str, ext: str) -> Path:
    if tipo not in NIVELES_VALIDOS:
        raise HTTPException(404, f"tipo inválido: {tipo} · usar {sorted(NIVELES_VALIDOS)}")
    safe_id = "".join(c for c in id_ if c.isalnum() or c in "-_")
    return INFORMES_DIR / tipo / f"{safe_id}.{ext}"


@router.get("/_index")
async def list_informes():
    """Lista todos los informes pre-renderizados disponibles."""
    if not INFORMES_DIR.exists():
        return {"total": 0, "por_tipo": {}, "items": []}
    items: list[dict] = []
    por_tipo: dict[str, int] = {}
    for tipo_dir in INFORMES_DIR.iterdir():
        if not tipo_dir.is_dir() or tipo_dir.name not in NIVELES_VALIDOS:
            continue
        n = 0
        for html in tipo_dir.glob("*.html"):
            items.append({"tipo": tipo_dir.name, "id": html.stem,
                          "size_kb": round(html.stat().st_size / 1024, 1)})
            n += 1
        por_tipo[tipo_dir.name] = n
    return {"total": len(items), "por_tipo": por_tipo, "items": items[:500]}


@router.get("/{tipo}/{id_}/data")
async def get_informe_data(tipo: str, id_: str):
    p = _path_for(tipo, id_, "json")
    if not p.exists():
        raise HTTPException(404, "datos no disponibles")
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))


@router.get("/{tipo}/{id_}/pdf")
async def get_informe_pdf(tipo: str, id_: str):
    """Lazy gen de PDF (WeasyPrint)."""
    pdf_path = _path_for(tipo, id_, "pdf")
    if pdf_path.exists():
        return FileResponse(pdf_path, media_type="application/pdf",
                            filename=f"informe_{tipo}_{id_}.pdf")
    html_path = _path_for(tipo, id_, "html")
    if not html_path.exists():
        raise HTTPException(404, "informe no pre-renderizado · ejecuta L12 batch primero")
    try:
        from weasyprint import HTML
    except ImportError as e:
        raise HTTPException(503, f"WeasyPrint no instalado · {e}")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_path.read_text(encoding="utf-8")).write_pdf(str(pdf_path))
    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=f"informe_{tipo}_{id_}.pdf")


@router.get("/{tipo}/{id_}/docx")
async def get_informe_docx(tipo: str, id_: str):
    """Lazy gen de DOCX (python-docx desde JSON canónico + LLM)."""
    docx_path = _path_for(tipo, id_, "docx")
    if docx_path.exists():
        return FileResponse(
            docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"informe_{tipo}_{id_}.docx",
        )
    json_path = _path_for(tipo, id_, "json")
    llm_path = _path_for(tipo, id_, "llm.json")
    if not json_path.exists():
        raise HTTPException(404, "datos no disponibles · ejecuta L12 batch primero")
    from app.services.informes_docx import build_docx
    data = json.loads(json_path.read_text(encoding="utf-8"))
    llm = json.loads(llm_path.read_text(encoding="utf-8")) if llm_path.exists() else {}
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    build_docx(data, llm, str(docx_path))
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"informe_{tipo}_{id_}.docx",
    )


@router.get("/{tipo}/{id_}", response_class=HTMLResponse)
async def get_informe_html(tipo: str, id_: str):
    p = _path_for(tipo, id_, "html")
    if not p.exists():
        raise HTTPException(404, f"informe no pre-renderizado · ejecuta L12 batch · esperado: {p.relative_to(BACKEND_ROOT)}")
    return HTMLResponse(p.read_text(encoding="utf-8"))
