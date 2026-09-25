import random
from datetime import date, timedelta

RANDOM_SEED = 42
CONDICIONES = ["despejado", "nublado", "lluvia_ligera", "lluvia_fuerte"]
MULTIPLICADOR_CLIMA = {
    "despejado": 1.0,
    "nublado": 0.85,
    "lluvia_ligera": 0.5,
    "lluvia_fuerte": 0.15,
}
FRANJAS = [8, 10, 12, 14, 16, 18]


def curva_base_por_hora(hora: int) -> float:
    if hora < 8 or hora > 18:
        return 0
    return max(0, 40 - abs(hora - 12) * 5)


def generar_registro(fecha: date, hora: int) -> dict:
    condicion = random.choices(CONDICIONES, weights=[0.45, 0.30, 0.18, 0.07])[0]
    temperatura = round(random.uniform(18, 30), 1)
    es_finde = fecha.weekday() >= 5
    base = curva_base_por_hora(hora) * MULTIPLICADOR_CLIMA[condicion]
    base *= 1.4 if es_finde else 1.0
    ruido = random.uniform(0.8, 1.2)
    visitantes = max(0, round(base * ruido))
    return {
        "fecha": fecha,
        "hora": hora,
        "temperatura_c": temperatura,
        "condicion_clima": condicion,
        "es_fin_de_semana": es_finde,
        "visitantes": visitantes,
    }


def generar_historico(dias: int = 365, inicio=None):
    random.seed(RANDOM_SEED)
    if inicio is None:
        inicio = date.today() - timedelta(days=dias)
    regs = []
    for d in range(dias):
        f = inicio + timedelta(days=d)
        for h in FRANJAS:
            regs.append(generar_registro(f, h))
    return regs


if __name__ == "__main__":
    import sys
    regs = generar_historico()
    print(f"registros={len(regs)} ejemplo={regs[0]}")
    if "--check" in sys.argv:
        assert len(regs) == 365 * 6 == 2190
        assert all(r["hora"] in FRANJAS for r in regs)
        assert all(0 <= r["visitantes"] <= 70 for r in regs)
        print("seed check OK")
