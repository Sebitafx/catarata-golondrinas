import json
import os
import pickle
from datetime import datetime

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.seed_data import generar_historico, RANDOM_SEED  # noqa: E402
from app.prediction import features  # noqa: E402


def main():
    regs = generar_historico()
    X = [features(r["hora"], r["temperatura_c"], r["condicion_clima"], r["es_fin_de_semana"]) for r in regs]
    y = [r["visitantes"] for r in regs]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)
    model = LinearRegression()
    model.fit(Xtr, ytr)
    rmse = float(((sum((a - b) ** 2 for a, b in zip(yte, model.predict(Xte))) / len(yte)) ** 0.5))
    out = os.getenv("MODEL_PATH", os.path.join(os.path.dirname(__file__), "..", "app", "model.pkl"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(model, f)
    meta = {"rmse": rmse, "n": len(regs), "fecha": datetime.now().isoformat(), "seed": RANDOM_SEED}
    with open(os.path.join(os.path.dirname(os.path.abspath(out)), "model_meta.json"), "w") as f:
        json.dump(meta, f)
    print(f"modelo guardado en {out} rmse={rmse:.2f} n={len(regs)}")


if __name__ == "__main__":
    main()
