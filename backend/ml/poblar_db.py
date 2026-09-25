"""Puebla backend/app/historico.db con el histórico sintético (S-5 spec).

Uso:  cd backend && python -m ml.poblar_db
Idempotente: si ya hay filas, no duplica.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, engine, TestingSessionLocal  # noqa: E402
from app.models import HistoricoVisita  # noqa: E402
from ml.seed_data import generar_historico  # noqa: E402


def main():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    existentes = db.query(HistoricoVisita).count()
    if existentes:
        print(f"ya hay {existentes} filas, no se duplica")
        return
    regs = generar_historico()
    for r in regs:
        db.add(HistoricoVisita(**r))
    db.commit()
    print(f"insertadas {len(regs)} filas en historico.db")


if __name__ == "__main__":
    main()
