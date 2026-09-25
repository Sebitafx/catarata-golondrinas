import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models
from .auth import require_admin_key
from .database import Base, engine, get_db
from .schemas import ClimaActual, HistoricoCreate, HistoricoOut, HistoricoPaginado, PrediccionOut, PronosticoOut
from .weather_client import WeatherServiceError, get_actual, get_pronostico
from . import prediction as pred_mod

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catarata Las Golondrinas API", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/clima/actual", response_model=ClimaActual)
async def clima_actual():
    try:
        return await get_actual()
    except WeatherServiceError as e:
        raise HTTPException(status_code=503, detail="servicio de clima no disponible, intente mas tarde")


@app.get("/api/clima/pronostico", response_model=PronosticoOut)
async def clima_pronostico(horas: int = Query(default=8, ge=1, le=8)):
    try:
        return await get_pronostico(horas)
    except WeatherServiceError:
        raise HTTPException(status_code=503, detail="servicio de clima no disponible, intente mas tarde")


@app.get("/api/prediccion", response_model=PrediccionOut)
async def prediccion(
    hora: int | None = Query(default=None, ge=0, le=23),
    fecha: date | None = Query(default=None),
):
    lima = ZoneInfo("America/Lima")
    ahora = datetime.now(lima)
    h = hora if hora is not None else ahora.hour
    f = fecha or ahora.date()
    es_finde = f.weekday() >= 5

    try:
        clima = await get_actual()
    except WeatherServiceError:
        raise HTTPException(status_code=503, detail="servicio de clima no disponible, intente mas tarde")

    if h < pred_mod.HORARIO_APERTURA or h > pred_mod.HORARIO_CIERRE:
        return {
            "hora": h,
            "fecha": f.isoformat(),
            "es_fin_de_semana": es_finde,
            "clima_usado": {"temperatura_c": clima["temperatura_c"], "condicion": clima["condicion"]},
            "visitantes_estimados": 0,
            "aforo_max": pred_mod.AFORO_MAX,
            "nota": "fuera de horario 08-18",
        }
    try:
        est = pred_mod.predict(h, clima["temperatura_c"], clima["condicion"], es_finde)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="modelo no entrenado, ejecute train_model.py")
    return {
        "hora": h,
        "fecha": f.isoformat(),
        "es_fin_de_semana": es_finde,
        "clima_usado": {"temperatura_c": clima["temperatura_c"], "condicion": clima["condicion"]},
        "visitantes_estimados": est,
        "aforo_max": pred_mod.AFORO_MAX,
        "nota": None,
    }


@app.get("/api/historico", response_model=HistoricoPaginado)
def listar_historico(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    q = db.query(models.HistoricoVisita).order_by(models.HistoricoVisita.fecha.desc(), models.HistoricoVisita.hora.desc())
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": items}


@app.post("/api/historico", response_model=HistoricoOut, status_code=201)
def crear_historico(payload: HistoricoCreate, ok: bool = Depends(require_admin_key), db: Session = Depends(get_db)):
    obj = models.HistoricoVisita(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/", include_in_schema=False)
def root():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"mensaje": "Catarata Las Golondrinas API, ver /docs"}
