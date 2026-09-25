import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sklearn.linear_model import LinearRegression
from ml.seed_data import generar_historico
from app import prediction as pred_mod


def _entrenar_tmp(tmp_path):
    regs = generar_historico(dias=30)
    X = [pred_mod.features(r["hora"], r["temperatura_c"], r["condicion_clima"], r["es_fin_de_semana"]) for r in regs]
    y = [r["visitantes"] for r in regs]
    m = LinearRegression().fit(X, y)
    import pickle
    p = str(tmp_path / "model_test.pkl")
    with open(p, "wb") as f:
        pickle.dump(m, f)
    os.environ["MODEL_PATH"] = p
    pred_mod._model = None
    return p


def test_rango_0_40(tmp_path):
    _entrenar_tmp(tmp_path)
    v = pred_mod.predict(12, 27.0, "despejado", False)
    assert 0 <= v <= 40


def test_lluvia_menos_que_despejado(tmp_path):
    _entrenar_tmp(tmp_path)
    a = pred_mod.predict(12, 26.0, "despejado", False)
    b = pred_mod.predict(12, 26.0, "lluvia_fuerte", False)
    assert b < a


def test_fuera_horario_cero(tmp_path):
    _entrenar_tmp(tmp_path)
    assert pred_mod.predict(3, 24.0, "despejado", False) == 0
    assert pred_mod.predict(22, 24.0, "despejado", False) == 0


def test_sin_modelo_error_controlado(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "noexiste.pkl"))
    pred_mod._model = None
    try:
        pred_mod.predict(12, 26.0, "despejado", False)
        assert False, "debió lanzar FileNotFoundError"
    except FileNotFoundError as e:
        assert "no entrenado" in str(e)
