import math
import os
import pickle
from pathlib import Path

HORARIO_APERTURA = 8
HORARIO_CIERRE = 18
AFORO_MAX = 40

_model = None


def features(hora: int, temperatura_c: float, condicion: str, es_finde: bool):
    ang = 2 * math.pi * hora / 24
    return [
        math.sin(ang),
        math.cos(ang),
        float(temperatura_c),
        1.0 if condicion == "nublado" else 0.0,
        1.0 if condicion == "lluvia_ligera" else 0.0,
        1.0 if condicion == "lluvia_fuerte" else 0.0,
        1.0 if es_finde else 0.0,
    ]


def model_path() -> str:
    default = str(Path(__file__).parent / "model.pkl")
    return os.getenv("MODEL_PATH", default)


def load_model():
    global _model
    if _model is not None:
        return _model
    path = model_path()
    if not os.path.exists(path):
        raise FileNotFoundError("modelo no entrenado, ejecute train_model.py")
    with open(path, "rb") as f:
        _model = pickle.load(f)
    return _model


def predict(hora: int, temperatura_c: float, condicion: str, es_finde: bool) -> int:
    if hora < HORARIO_APERTURA or hora > HORARIO_CIERRE:
        return 0
    model = load_model()
    x = [features(hora, temperatura_c, condicion, es_finde)]
    y = float(model.predict(x)[0])
    y = max(0, min(AFORO_MAX, round(y)))
    return int(y)
