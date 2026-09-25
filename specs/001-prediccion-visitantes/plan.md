# PLAN 001 — Cómo se implementa la predicción de visitantes

> Lee primero: `../constitution.md` y `./spec.md`. Este archivo es el CÓMO. No cambia el QUÉ sin actualizar `spec.md`.

---

## 1. Stack y constantes

| Capa | Decisión |
|------|----------|
| Backend | FastAPI Python 3.11+, `async` para clima |
| DB | SQLite vía SQLAlchemy (`backend/app/historico.db` local, no commiteado) |
| ML | scikit-learn `LinearRegression`, `RANDOM_SEED=42` |
| Clima | OpenWeatherMap Current Weather `https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={KEY}&units=metric&lang=es` |
| Frontend | HTML/CSS/JS vanilla en `backend/app/static/`, servido por FastAPI en `/` |
| Tests | `pytest + TestClient + pytest-cov`, mocks con `unittest.mock`, DB `sqlite:///:memory:` por test |
| Deploy | `venv + systemd` en EC2 Ohio, puerto `8000` |
| CI/CD | GitHub Actions `test → deploy` por SSH |

```ini
# Constantes de dominio (S-1..S-3 spec.md)
LAT=-8.7938
LON=-76.3348
HORARIO_APERTURA=8
HORARIO_CIERRE=18
AFORO_MAX=40
NOMBRE_LUGAR=Catarata Las Golondrinas, Rio Tigre, Huanuco
```

## 2. Estructura de carpetas objetivo

```text
catarata-golondrinas/
├── specs/
│   ├── constitution.md
│   └── 001-prediccion-visitantes/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI, monta /static, incluye routers
│   │   ├── database.py      # engine/session, get_db
│   │   ├── models.py        # ORM HistoricoVisita
│   │   ├── schemas.py       # Pydantic request/response
│   │   ├── weather_client.py# async httpx + normalización + cache 10min
│   │   ├── prediction.py    # carga model.pkl, features, clip 0..40
│   │   └── static/
│   │       ├── index.html
│   │       ├── styles.css
│   │       └── app.js
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── seed_data.py     # generador sintético S-5
│   │   └── train_model.py   # entrena y guarda ../app/model.pkl
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py      # TestClient + DB memoria + mock clima
│   │   ├── test_prediction.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── .env.example
├── .github/workflows/ci-cd.yml
├── .gitignore
└── README.md
```

## 3. Modelo de datos

Tabla `historico_visitas`:

| Campo | Tipo | Restricción | Nota |
|-------|------|-------------|------|
| `id` | int PK autoincrement | PK | |
| `fecha` | date | not null | ej. `2026-09-25` |
| `hora` | int | 0-23, not null | consulta/predicción usa 8-18, fuera = 0 |
| `temperatura_c` | float | not null | 18-30 típico selva |
| `condicion_clima` | str enum | `despejado/nublado/lluvia_ligera/lluvia_fuerte` | normalizado desde OpenWeather |
| `es_fin_de_semana` | bool | not null | derivado de `fecha.weekday()>=5` si no se envía |
| `visitantes` | int | >=0, <=200 (DB admite, API recorta a 40 en predicción) | variable objetivo |

Índice compuesto `(fecha, hora)` para seed idempotente.

## 4. Contratos de API (C5 constitución)

### 4.1 `GET /health`
```json
// 200 siempre, sin depender de clima ni modelo
{"status": "ok"}
```

### 4.2 `GET /api/clima/actual`
Proxy + normalización + cache 10 min en memoria.

```json
// 200
{
  "temperatura_c": 26.4,
  "condicion": "nublado",
  "descripcion": "nubes dispersas",
  "humedad": 78,
  "hora_consulta": "2026-09-25T15:00:00-05:00",
  "fuente": "openweathermap",
  "lat": -8.7938,
  "lon": -76.3348
}
// 503 si OpenWeather cae
{"detail": "servicio de clima no disponible, intente mas tarde"}
```

Mapeo OpenWeather `main` → enum:
`Clear→despejado, Clouds→nublado, Drizzle→lluvia_ligera, Rain (<=2.5mm/h)→lluvia_ligera, Rain (>2.5mm/h)/Thunderstorm→lluvia_fuerte, default→nublado`.

### 4.2b `GET /api/clima/pronostico?horas=8` (misma API/key, sin servicio nuevo)
Proxy a OpenWeather `GET /data/2.5/forecast?lat&lon&appid&units=metric&lang=es` (bloques 3h, gratis). Normaliza cada bloque con el mismo `mapear_condicion`, devuelve hasta `horas` bloques (1-8, default 8 ≈ 24h).
```json
// 200
{"fuente": "openweathermap", "bloques": [
  {"hora_consulta": "2026-09-25T18:00:00-05:00", "temperatura_c": 27.1, "condicion": "lluvia_ligera", "descripcion": "lluvia ligera", "humedad": 80},
  {"hora_consulta": "2026-09-25T21:00:00-05:00", "temperatura_c": 24.3, "condicion": "nublado", "descripcion": "nublado", "humedad": 88}
]}
// 503 si OpenWeather cae
{"detail": "servicio de clima no disponible, intente mas tarde"}
```
Uso: el dashboard pinta la tira de pronóstico y a futuro puede alimentar `/api/prediccion` por hora con el clima del bloque más cercano (no solo clima actual).

### 4.3 `GET /api/prediccion?hora=12&fecha=2026-09-27`
- `hora`: optional int 0-23, default hora actual Lima (`America/Lima`, UTC-5).
- `fecha`: optional `YYYY-MM-DD`, default hoy. Sirve para calcular `es_fin_de_semana`.

```json
// 200 dentro de horario
{
  "hora": 12,
  "fecha": "2026-09-27",
  "es_fin_de_semana": true,
  "clima_usado": {"temperatura_c": 26.4, "condicion": "despejado"},
  "visitantes_estimados": 38,
  "aforo_max": 40,
  "nota": null
}
// 200 fuera de horario
{
  "hora": 3, "fecha": "2026-09-27", "es_fin_de_semana": false,
  "clima_usado": {"temperatura_c": 22.0, "condicion": "nublado"},
  "visitantes_estimados": 0, "aforo_max": 40,
  "nota": "fuera de horario 08-18"
}
```

Flujo: `weather_client.get_actual() → prediction.predict(hora, temp, condicion, finde) → clip 0..40 → round int`. Si clima falla → intenta cache; si no hay cache → `503`. Si `model.pkl` falta → `503 {"detail":"modelo no entrenado, ejecute train_model.py"}` (C2 constitución, error controlado, no crash).

### 4.4 `GET /api/historico?page=1&size=20`
```json
{"total": 2190, "page": 1, "size": 20, "items": [
  {"id":1,"fecha":"2025-09-25","hora":8,"temperatura_c":24.5,"condicion_clima":"despejado","es_fin_de_semana":false,"visitantes":18}
]}
```

### 4.5 `POST /api/historico` (protegido escritura mínima)
Header requerido: `X-Admin-Key: <ADMIN_KEY del .env>` (comparación `secrets.compare_digest`, dependencia `require_admin_key`).
```json
// request headers: X-Admin-Key: secret-demo
// request body
{"fecha":"2026-09-25","hora":12,"temperatura_c":27.1,"condicion_clima":"despejado","es_fin_de_semana":false,"visitantes":34}
// 201 igual + id
// 401 sin header o inválida: {"detail":"no autorizado"}
// 422 si hora fuera 0-23, condicion fuera de enum, visitantes <0
```
`GET /api/historico` sigue público sin key. Dashboard hace `POST` solo desde sección admin (prompt de clave guardada en `sessionStorage`, nunca hardcodeada).

### 4.6 `GET /` + `/docs`
- `/` público sin login, **modo oscuro por defecto** (`body.dark`, toggle a claro con `localStorage`), **fecha auto = hoy Lima** (sin input fecha, no se predice pasado), hero + ficha + **fotos reales** `static/img/lugar-catarata.jpg` (cascada) y `lugar-poza.jpg` (poza/acceso) con fallback a HD/SVG, clima actual + tira pronóstico 24h + selector solo hora con botón `Predecir afluencia` + próximas 3 franjas + últimos 10 históricos en **tabla** (`fecha|hora|visitantes|clima|temp`) + sección admin colapsable para `POST` con `X-Admin-Key`.
- `/docs` Swagger automático.

## 5. Features del modelo ML

Input vector (7 dims):
`[hora_sin, hora_cos, temperatura_c, nublado, lluvia_ligera, lluvia_fuerte, es_finde]`
(`despejado` es baseline con los 3 one-hot en 0; `hora_sin/cos = sin/cos(2*pi*hora/24)`).

Por qué cada una: hora explica curva mediodía; temp correlaciona con día soleado; clima one-hot captura caída por lluvia; finde captura x1.4.

Entrenamiento: `train_model.py` lee SQLite (o CSV intermedio), `train_test_split 80/20 random_state=42`, `LinearRegression`, guarda `backend/app/model.pkl` + `model_meta.json` (rmse, fecha, n).

Seed sintético (S-5): campana `max(0,40-abs(hora-12)*5)` en 8-18, `x1.0/0.85/0.5/0.15` por clima, `x1.4` finde, ruido `uniform 0.8-1.2`, `temp uniform 18-30`. Genera 365 días x 6 franjas (8,10,12,14,16,18) = 2190 + valida tope.

## 6. `weather_client.py` — resiliencia (RNF-2)

- `httpx.AsyncClient timeout=5s`, 1 reintento.
- Cache dict `{data, timestamp}` TTL 600s.
- `get_actual()` lanza `WeatherServiceError` → router convierte a `503`.
- Tests nunca llaman red real: `mock get_actual` o `respx/mock httpx`.

## 7. Testing

- `conftest.py`: `engine sqlite:///:memory:`, `TestingSessionLocal`, override `get_db`, fixture `client`.
- `test_prediction.py`: rango 0..40, lluvia_fuerte<despejado, fuera horario=0, sin model.pkl no crash.
- `weather_client.py`: `get_actual()` (current) + `get_pronostico(horas)` (forecast 3h, mismo mapeo, sin cache o TTL 30min por bloque).
- `test_api.py`: `/health 200`, `/api/clima/actual 200 mock + 503 mock error`, `/api/clima/pronostico?horas=2 200 mock + 503`, `/api/prediccion?hora=12 200 + ?hora=3 0`, `POST /historico 201 con key + 401 sin/inválida + 422 datos mal`, `GET /historico paginado público`, `GET / 200`.
- Comando: `pytest backend/tests --cov=backend/app --cov-report=term-missing -v`.

## 8. Config y secretos (C3)

`.env.example`:
```ini
OPENWEATHER_API_KEY=
ADMIN_KEY=cambia-esta-clave-demo
LAT=-8.7938
LON=-76.3348
DATABASE_URL=sqlite:///./app/historico.db
MODEL_PATH=./app/model.pkl
```
Auth: `app/auth.py` con `require_admin_key(request: Request)` lee `X-Admin-Key` y compara con `os.getenv("ADMIN_KEY")`; si falta env en tests usa `test-admin-key`. Sin tabla users.
`.gitignore`: `.env, *.db, *.pkl, .venv/, __pycache__/, .pytest_cache/, model_meta.json`.

## 9. Despliegue EC2 + CI/CD (resumen, detalle en T11-T12)

- AMI Ubuntu 24.04, `t2.micro/t3.micro`, SG abre `8000/tcp` + `22/tcp` (demo curso).
- `systemd catarata-app.service` con `EnvironmentFile`, `Restart=always`, `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Actions: `test` (setup-python 3.11, `pip install -r backend/requirements.txt --no-cache-dir`, pytest) → `deploy` solo push main (appleboy/ssh-action, `git pull + pip install + restart`).

## 10. Decisiones descartadas

| Decisión | Descartada | Por qué |
|----------|------------|---------|
| Postgres/RDS | No v1 | Overkill 1 instancia, costo, SQLite basta + SQLAlchemy migra después |
| RandomForest/XGBoost | No v1 | Menos explicable para curso, más RAM; LinearRegression ya es estadística real |
| Docker | Opcional | 1GB RAM + overhead; systemd da restart+logs suficientes |
| Open-Meteo | Plan B | Sin key, pero se eligió OpenWeather por valor pedagógico de secretos; adaptador posible a futuro |
| React SPA | No | Build complica deploy; vanilla JS suficiente para HU-3 |
| Login JWT / tabla users | No v1 | Overkill para 1 endpoint escritura; `X-Admin-Key` da anti-vandalismo sin registro ni fricción turista; JWT queda como `002` futuro si el docente lo pide |
