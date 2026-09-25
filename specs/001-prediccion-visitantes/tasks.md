# TASKS 001 — Desglose verificable

> Cada tarea referencia `RF-*` de `spec.md` y sección de `plan.md`. Orden de ejecución estricto. No saltar sin test verde previo. Marcar `[x]` solo con evidencia (`pytest` o `curl`).

---

## Fase A — Base

- [ ] **T1: Scaffold FastAPI + estructura** — Crea `backend/app/{main,database,models,schemas,static}/`, `backend/ml/`, `backend/tests/`, `requirements.txt` (fastapi, uvicorn, sqlalchemy, pydantic, httpx, scikit-learn, pytest, pytest-cov), `.env.example`, `.gitignore`. `RF-6` parcial.
  - Aceptación: `uvicorn app.main:app` levanta y `GET /health` → `{"status":"ok"}`.
  - Test: `test_api.py::test_health`.

- [ ] **T2: Modelo SQLAlchemy + SQLite** — `models.HistoricoVisita` según plan §3 + `database.get_db` + índice `(fecha,hora)`. `RF-3/RF-4`.
  - Aceptación: crear + leer 1 registro en DB memoria.
  - Test: fixture `conftest.py` + test modelo.

- [ ] **T3: Seed sintético** — `ml/seed_data.py` con curva base mediodía, multiplicadores clima, x1.4 finde, ruido, `RANDOM_SEED=42`, 365d x 6 franjas 08-18. `S-5, RF-4`.
  - Aceptación: genera ~2190 registros, todos `hora in [8,10,12,14,16,18]`, `0<=visitantes<=70` crudo (pico 40 x1.4 finde x1.2 ruido ≈ 67, luego `prediction.py` recorta a 40).
  - Test: `test_seed.py` o asserts en script `--check` (conteo + rango + reproducibilidad).

## Fase B — Clima

- [ ] **T4: `weather_client.py`** — `async get_actual()` httpx timeout 5s, mapeo enum, cache TTL 600s, `WeatherServiceError`. `RF-1, RNF-2`.
  - Aceptación: con mock httpx retorna normalizado; con timeout lanza `WeatherServiceError`.
  - Test: unit con `unittest.mock` (nunca red real).

- [ ] **T5: `GET /api/clima/actual`** — Router + `503` en `WeatherServiceError`. `RF-1, HU-1`.
  - Aceptación: `200` con JSON plan §4.2; `503` con mock caído; `/health` sigue 200.
  - Test: `test_api clima_200 + clima_503`.

## Fase C — Predicción (core 70%)

- [ ] **T6: `train_model.py`** — Lee DB, features plan §5, split 80/20 `random_state=42`, `LinearRegression`, guarda `app/model.pkl + model_meta.json`. `RF-2, RNF-4`.
  - Aceptación: `rmse < 8` en sintético, re-run mismo hash.
  - Test: entrena en memoria pequeña y verifica `model.pkl` existe + predict no NaN.

- [ ] **T7: `prediction.py`** — `load_model()` lazy + `predict(hora,temp,condicion,finde)` con cíclica hora, `clip 0..40`, `hora<8 o >18 → 0`. `RF-2, RNF-5`.
  - Aceptación: `lluvia_fuerte < despejado` igual hora; `hora=3 → 0`; sin pkl → excepción controlada.
  - Test: `test_prediction.py` (4 casos borde C2).

- [ ] **T8: `GET /api/prediccion`** — Query `hora,fecha`, deriva `finde`, llama clima + predicción, fallback cache/503. `RF-2, HU-2`.
  - Aceptación: ejemplos JSON plan §4.3 exactos.
  - Test: `test_api prediccion_200 + fuera_horario_0 + clima_caido_503`.

## Fase D — Histórico + Frontend

- [ ] **T9: `GET/POST /api/historico` con protección mínima** — `GET` público con paginación `page/size`; `POST` exige `X-Admin-Key` (`require_admin_key`, `401` sin/inválida, `201` válida, `422` datos mal). `RF-3/RF-4, HU-4, S-6`.
  - Aceptación: `GET` sin key 200; `POST` sin key 401 nada persiste; con key válida 201 y aparece en `GET`; inválido 422.
  - Test: `test_api historico_public_get + post_401 + post_201 + post_422`.

- [ ] **T10: Dashboard `/` público** — `static/index.html/css/js` **modo oscuro default** + hero + ficha + **fotos reales** `lugar-catarata.jpg/lugar-poza.jpg` (fallback HD/SVG) + reloj Lima + clima actual + tira pronóstico + selector solo `hora` (**fecha auto hoy**, no pasado) con botón `Predecir` + 3 franjas + últimos 10 en **tabla** + admin `X-Admin-Key` en `sessionStorage`. `RF-5, HU-3, RNF-8`.
  - Aceptación: `GET / 200 text/html`, JS sin framework, funciona con API caída (mensaje amable).
  - Test: `test_api root_200` contiene `id="clima"`, `id="prediccion"`, `id="btn-predecir"`, `id="ficha-lugar"` y `id="fecha-auto"`.

- [ ] **T13: Pronóstico clima 24h (misma API/key)** — `weather_client.get_pronostico(horas)` a OpenWeather `forecast` + `GET /api/clima/pronostico?horas` con `503` si cae + tira en dashboard. `RF-7, HU-1`.
  - Aceptación: `?horas=2` retorna 2 bloques normalizados; sin key/red → `503`, `/health` 200.
  - Test: `test_api pronostico_200 + pronostico_503` con mock (nunca red real).

## Fase E — Deploy + CI/CD

- [ ] **T11: Systemd + docs deploy** — `deploy/catarata-app.service`, `README.md` con pasos EC2 (Ubuntu 24.04, `python3.11-venv`, `pip install --no-cache-dir`, `.env`, `enable --now`), verificación `/docs`. `RNF-6/RNF-7`.
  - Aceptación: checklist manual + `journalctl -u catarata-app` documentado.
  - Test: no código, evidencia `curl http://<IP>:8000/health`.

- [ ] **T12: GitHub Actions `test→deploy`** — `.github/workflows/ci-cd.yml` según plan §9, secrets `EC2_HOST/EC2_USER/EC2_SSH_KEY/OPENWEATHER_API_KEY`. `C6`.
  - Aceptación: push a `main` con tests verdes despliega; PR solo testea.
  - Test: pipeline verde en GitHub (screenshot para docente).

---

## Matriz trazabilidad

| Task | RF | Tests |
|------|----|-------|
| T1 | RF-6 | test_health |
| T2 | RF-3/4 | fixture + modelo |
| T3 | S-5/RF-4 | seed check |
| T4 | RF-1 | unit weather mock |
| T5 | RF-1 | api clima 200/503 |
| T6 | RF-2 | train + rmse |
| T7 | RF-2 | prediction 4 bordes |
| T8 | RF-2 | api prediccion |
| T9 | RF-3/4 | api historico get público + post 201/401/422 |
| T10 | RF-5 | api root con ficha + btn-predecir + fecha-auto + tabla historico |
| T13 | RF-7 | api pronostico 200/503 |
| T11 | RNF-6/7 | curl EC2 |
| T12 | C6 | pipeline verde |

Siguiente paso tras aprobar specs: ejecutar `T1`, luego `T2`... sin saltar. Cada `T` pide revisión antes del siguiente.
