# 🌊 Catarata Las Golondrinas — Predicción de visitantes según clima y hora

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![scikit-learn](https://img.shields.io/badge/scikit--learn-LinearRegression-orange?logo=scikitlearn)
![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?logo=sqlite)
![pytest](https://img.shields.io/badge/pytest-11%20passed-brightgreen?logo=pytest)
![EC2](https://img.shields.io/badge/AWS-EC2%20Ohio-orange?logo=amazonec2)
![CI/CD](https://img.shields.io/badge/GitHub_Actions-test→deploy-blue?logo=githubactions)
![SDD](https://img.shields.io/badge/Spec--Driven-constitution→tasks-purple)

> **Objetivo principal:** predecir cuántos visitantes se esperan en la catarata combinando **clima actual + pronóstico + hora del día** con un modelo de regresión entrenado sobre un histórico. El turista decide si ir ahora o más tarde; el administrador anticipa afluencia para personal y seguridad en una poza pequeña.

**Atractivo asignado:** Catarata Las Golondrinas — Caserío Río Tigre, distrito Mariano Dámaso Beraún, provincia Leoncio Prado, departamento de Huánuco, Perú.
**Acceso:** 20 min en carro desde Tingo María + 8 min de caminata por el bosque · **Altitud:** ~1 022 msnm · **Caída:** ~15 m ·
**Coords:** `-8.7938, -76.3348` · **Horario (supuesto validado en sitio):** 08:00–18:00 · **Aforo práctico:** 40 personas (sin valor oficial MINCETUR).

**Autor:** Josué Sebastián Oriundo Tafur · **Curso:** Desarrollo de Aplicaciones para la Nube

---

## 📑 Tabla de contenido

- [Demo](#-demo)
- [¿Qué predice y cómo?](#-qué-predice-y-cómo)
- [Specs (documentación que evalúa el docente)](#-specs-documentación-que-evalúa-el-docente)
- [Arquitectura](#-arquitectura)
- [API](#-api)
- [Estructura](#-estructura)
- [Banco de datos](#-banco-de-datos-dónde-está-y-de-dónde-viene)
- [Inicio rápido local](#-inicio-rápido-local)
- [Tests](#-tests)
- [Despliegue en AWS EC2](#-despliegue-en-aws-ec2)
- [CI/CD con GitHub Actions](#-cicd-con-github-actions)
- [Video de evidencia en producción](#-video-de-evidencia-en-producción)
- [Roadmap](#-roadmap)

## 🚀 Demo

| Entorno | URL |
|---|---|
| Local | `http://localhost:8000/` (dashboard) · `http://localhost:8000/docs` (Swagger) |
| Producción EC2 | `http://3.148.214.177:8000/` (dashboard) · `http://3.148.214.177:8000/docs` (Swagger) |

## 🔮 ¿Qué predice y cómo?

1. **Clima actual** (`OpenWeatherMap`, misma key): temperatura + condición normalizada a `despejado / nublado / lluvia_ligera / lluvia_fuerte`, con caché de 10 min y fallback `503` sin tumbar la app.
2. **Pronóstico 24 h** (misma API/key, endpoint `forecast`, sin servicio nuevo): 8 bloques de 3 h para la tira del dashboard y futura predicción por hora.
3. **Aforo esperado**: `LinearRegression` (scikit-learn, `RANDOM_SEED=42`) sobre features `[hora_sin, hora_cos, temperatura, nublado, lluvia_ligera, lluvia_fuerte, es_finde]` → entero `0–40` (tope aforo práctico; fuera de `08–18` → `0`).
4. **Dato honesto para la defensa**: sin datos reales, el histórico inicial es sintético (~2190 registros, campana al mediodía × clima × 1.4 finde + ruido). El modelo aprende esa función; sirve como demo de curso, no como ML productivo. `POST /api/historico` (protegido con `X-Admin-Key`, sin JWT en v1) permite corregirlo con datos reales.

## 📐 Specs (documentación que evalúa el docente)

Metodología **Spec-Driven Development**: specs primero, código después. Trazabilidad `RF → task → test`, sin RF huérfanos.

| Archivo | Rol |
|---|---|
| [`specs/constitution.md`](specs/constitution.md) | 8 principios no negociables (tests por endpoint, casos borde, secretos nunca commiteados, semilla fija, contrato antes que código, no deploy si falla, trazabilidad, supuestos explícitos) |
| [`specs/001-prediccion-visitantes/spec.md`](specs/001-prediccion-visitantes/spec.md) | El QUÉ (70 % del proyecto): contexto Río Tigre, HU-1…HU-4 con Given/When/Then, RF-1…RF-7, RNF-1…RNF-8, supuestos S-1…S-6, fuera de alcance |
| [`specs/001-prediccion-visitantes/plan.md`](specs/001-prediccion-visitantes/plan.md) | El CÓMO: modelo de datos, contratos con JSON de ejemplo, features ML, resiliencia, decisiones descartadas |
| [`specs/001-prediccion-visitantes/tasks.md`](specs/001-prediccion-visitantes/tasks.md) | T1…T13 verificables una por una con su test |

## 🏗 Arquitectura

```text
Turista/Admin ──► Dashboard estático (dark default, fecha auto hoy Lima, fotos reales)
                      │  /api/clima/actual · /api/clima/pronostico · /api/prediccion?hora
                      ▼
              FastAPI (async httpx) ──► OpenWeatherMap (current + forecast, misma key)
                      │  prediction.py (model.pkl, clip 0–40)   auth.py (X-Admin-Key solo POST)
                      ▼
              SQLite vía SQLAlchemy (historico_visitas) ──► seed sintético + train LinearRegression
```

## 🔌 API

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| `GET` | `/health` | — | `{"status":"ok"}`, no depende de clima ni modelo |
| `GET` | `/api/clima/actual` | — | Clima actual normalizado (+ caché 10 min). `503` si cae OpenWeather |
| `GET` | `/api/clima/pronostico?horas=8` | — | 1–8 bloques 3 h (~24 h). Misma API/key |
| `GET` | `/api/prediccion?hora=12` | — | `visitantes_estimados 0–40`; fecha auto = hoy Lima; fuera de `08–18` → `0` |
| `GET` | `/api/historico?page=1&size=20` | — | Paginado público |
| `POST` | `/api/historico` | `X-Admin-Key` | `201` válida · `401` sin/inválida · `422` datos mal |
| `GET` | `/` | — | Dashboard (ficha, reloj vivo, clima, pronóstico, botón Predecir, tabla históricos) |
| `GET` | `/docs` | — | Swagger automático |

## 🗂 Estructura

```text
├── specs/constitution.md + 001-prediccion-visitantes/{spec,plan,tasks}.md
├── backend/{app/{main,database,models,schemas,auth,weather_client,prediction,static/},ml/{seed_data,train_model},tests/}
├── deploy/catarata-app.service   # systemd EC2
├── .github/workflows/ci-cd.yml  # test → deploy
├── docs/                        # video de evidencia en producción (ver docs/README.md)
└── README.md
```

## 🗄 Banco de datos (dónde está y de dónde viene)

> Requisito del docente: el proyecto cuenta con banco de datos propio (creado por nosotros) + clima externo vía web (OpenWeatherMap).

| Punto | Detalle |
|---|---|
| **Motor** | SQLite vía SQLAlchemy (cero servidor, ideal EC2 free-tier; migrable a PostgreSQL/RDS sin cambiar el ORM) |
| **Archivo** | `backend/app/historico.db` (generado localmente y en EC2, **no se commitea** por `.gitignore`) |
| **Tabla** | `historico_visitas(id, fecha, hora, temperatura_c, condicion_clima, es_fin_de_semana, visitantes)` + índice `(fecha, hora)` |
| **Origen** | Sintético pero plausible: `backend/ml/seed_data.py` genera ~2190 registros (365 días × 6 franjas 08–18h, campana al mediodía × clima × 1.4 finde + ruido, `RANDOM_SEED=42`) y los inserta en SQLite; luego `train_model.py` entrena la regresión |
| **Datos reales** | Entran por `POST /api/historico` (protegido con `X-Admin-Key`) para corregir el modelo con el tiempo |

```bash
# Regenerar el banco desde cero
cd backend
python -m ml.seed_data --check   # verifica 2190 registros en memoria
python -m ml.poblar_db           # inserta 2190 filas en app/historico.db (idempotente)
python -m ml.train_model         # deja app/model.pkl + model_meta.json (rmse≈5)
```

Verlo: extensión `SQLite Viewer` de VSCode / `DB Browser for SQLite` abriendo `backend/app/historico.db`, o en vivo `GET /api/historico?page=1&size=20` y el dashboard (tabla Últimos históricos).

## ⚡ Inicio rápido local

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # completa OPENWEATHER_API_KEY y ADMIN_KEY
python -m ml.train_model
uvicorn app.main:app --reload --port 8000
# http://localhost:8000/ · http://localhost:8000/docs
```

## ✅ Tests

```bash
pytest backend/tests --cov=backend/app --cov-report=term-missing -v
# 11 passed: health, clima 200/503, pronostico 200/503, prediccion + fuera-horario,
# historico 401/201/422, root con marcadores, predicción rango/fuerte<despejado/cero/modelo-faltante
```

## ☁️ Despliegue en AWS EC2

Ubuntu 24.04 `t2.micro/t3.micro` (Ohio), SG `22/tcp + 8000/tcp`, `venv + systemd` (sin Docker por RAM):

```bash
sudo apt update && sudo apt install -y python3-venv git
git clone <tu-repo> catarata-golondrinas && cd catarata-golondrinas/backend
python3 -m venv .venv && source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
cp .env.example .env  # edita keys reales
python -m ml.train_model
sudo cp ../deploy/catarata-app.service /etc/systemd/system/
sudo systemctl enable --now catarata-app
curl http://<IP>:8000/health  # → {"status":"ok"}
```

## 🔁 CI/CD con GitHub Actions

Workflow [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml): en cada `push`/PR corre **`test`** (`setup-python 3.11` + `pytest`); solo si pasa y el push fue a `main`, corre **`deploy`** por SSH (`git pull + pip install + train + systemctl restart`). Secrets: `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `OPENWEATHER_API_KEY`, `ADMIN_KEY` (`Settings → Secrets and variables → Actions`).

## 🎬 Video de evidencia en producción

Ver [`docs/README.md`](docs/README.md): tras el deploy se sube ahí el video (haciendo un cambio, `push`, Actions en verde y app respondiendo en la IP de EC2).

## 🗺 Roadmap

- `002`: alimentar `/api/prediccion` futura con el bloque de pronóstico más cercano (no solo clima actual).
- Fotos propias Full HD del lugar en `static/img/lugar-*.jpg` (hoy placeholders + 2 reales pendientes de guardar).
- Reentrenamiento con datos reales vía `POST /api/historico`.
