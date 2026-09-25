# Prompt Contextualizador — App "Catarata las Golondrinas"
### Predicción de visitantes según clima y hora — Metodología SDD

---

## 0. Cómo usar este documento

1. Todo este documento es tuyo para editar — ajusta lo que marco como `⚠️ CONFIRMAR`.
2. La **Sección 9** trae el prompt literal, listo para copiar y pegar como primer mensaje en OpenCode.
3. Empieza en **modo Plan** (ver Sección 10) — no dejes que el agente escriba código hasta que apruebes spec → plan → tasks.
4. Este documento en sí *es* tu punto de partida de las specs. El agente las va a expandir, no a inventarlas desde cero.

---

## 1. Resumen del proyecto

| | |
|---|---|
| **Curso** | Desarrollo de Aplicaciones para la Nube |
| **Atractivo turístico** | Catarata las Golondrinas (región Huánuco, cerca de Tingo María, Perú) |
| **Objetivo** | Una app que consulta el clima actual del lugar y, combinando clima + hora del día, predice cuántos visitantes se esperan, usando un histórico de visitantes/temperatura por día |
| **Metodología** | Spec-Driven Development (SDD) — specs primero, código después |
| **Infraestructura** | AWS EC2 (ya tienes instancia en Ohio, free tier) |
| **CI/CD** | GitHub Actions |
| **Entregables** | specs versionadas, API funcional, tests automatizados, app corriendo en EC2, pipeline verde en GitHub |

---

## 2. Stack tecnológico definido

| Capa | Tecnología | Por qué |
|---|---|---|
| Backend / API | **FastAPI** (Python 3.11+) | Tipado con Pydantic, docs automáticas (Swagger/OpenAPI) que sirven como evidencia para tu docente, fácil de testear con `TestClient`, y `async` nativo para llamar a la API de clima sin bloquear el servidor. |
| Base de datos | **SQLite** vía SQLAlchemy | Cero servidor que administrar, perfecta para una sola instancia EC2 free-tier, el archivo `.db` es reproducible. Si luego migran a PostgreSQL/RDS, SQLAlchemy hace el cambio casi transparente. |
| Predicción | **scikit-learn** (regresión) | `LinearRegression` sobre features de hora, temperatura y condición de clima — es una predicción estadística real (no un if-else disfrazado), pero sigue siendo explicable y manejable para el alcance del curso. |
| Clima externo | **OpenWeatherMap** (Current Weather Data API) | Ya tienes el patrón `.env` en tu `.gitignore`, y esta API es el estándar de facto en tutoriales — buena elección pedagógica porque te obliga a manejar secretos correctamente (tema central de un curso de cloud). Alternativa sin API key si prefieres cero fricción: **Open-Meteo**. |
| Frontend | HTML + CSS + JS simple, servido como estáticos por FastAPI | *Asumido* — no se definió explícitamente. Un dashboard de una sola página (clima actual + predicción) es suficiente para el alcance; no complica el despliegue con un build de React. Si tu docente pide SPA, cámbialo en `plan.md`. |
| Testing | pytest + `TestClient` de FastAPI + pytest-cov | Estándar del ecosistema Python/FastAPI. |
| Despliegue | venv + **systemd** (sin Docker por defecto) | Tu EC2 free-tier tiene 1 GB de RAM — Docker añade overhead que no necesitas para una sola app FastAPI. `systemd` te da reinicio automático y logs con `journalctl`. Docker queda como mejora opcional si el curso lo pide explícitamente. |
| CI/CD | GitHub Actions (2 jobs: test → deploy) | Corre tests en cada push/PR; despliega a EC2 por SSH solo si los tests pasan y es `main`. |

---

## 3. Ubicación de referencia ⚠️ CONFIRMAR

No hay coordenadas oficiales documentadas de "Catarata las Golondrinas" en fuentes públicas — parece ser un atractivo local, no uno masivamente indexado (Gocta, Yumbilla, etc. sí lo están, esta no).

Como punto de partida usa **Tingo María** (la ciudad más cercana con estación meteorológica confiable):

```
Latitud aproximada:  -9.2957
Longitud aproximada: -75.9975
```

**Ajusta esto** con las coordenadas reales de la catarata (Google Maps → clic derecho sobre el punto exacto → copiar coordenadas) y documéntalo como constante en el `plan.md`, no lo dejes hardcodeado sin explicar de dónde salió.

También define y documenta (tú la conoces, yo no):
- **Horario de atención real** del lugar ⚠️ CONFIRMAR (asumo 6:00–18:00 como placeholder para la Sección 5).
- **Aforo aproximado / capacidad máxima** ⚠️ CONFIRMAR (útil como tope superior razonable para que la predicción no dispare números absurdos).

---

## 4. Metodología SDD — flujo de trabajo

El ciclo SDD tiene 4 fases, cada una con un archivo entregable. **No se pasa a la siguiente fase sin revisar la anterior.**

```
specify  →  plan  →  tasks  →  implement
 (QUÉ)      (CÓMO)   (pasos)   (código)
```

Estructura de carpetas recomendada:

```
catarata-golondrinas/
├── specs/
│   ├── constitution.md
│   └── 001-prediccion-visitantes/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py         # SQLAlchemy ORM
│   │   ├── schemas.py        # Pydantic
│   │   ├── weather_client.py
│   │   ├── prediction.py
│   │   └── static/            # frontend simple
│   ├── ml/
│   │   ├── seed_data.py
│   │   └── train_model.py
│   ├── tests/
│   │   ├── test_prediction.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── .env.example
├── .github/workflows/ci-cd.yml
└── README.md
```

### 4.1 `constitution.md` — principios no negociables

Plantilla (pídele al agente que la complete y la respete en todo lo que sigue):

```markdown
# Constitución del proyecto — Catarata las Golondrinas

1. Todo endpoint público debe tener al menos un test de integración.
2. La lógica de predicción debe tener tests unitarios con casos borde
   (clima extremo, hora fuera de horario, sin datos históricos).
3. Ningún secreto (API keys, credenciales) se commitea. Van en `.env`
   (local) o GitHub Secrets (CI/CD). `.env.example` sí se versiona.
4. El entrenamiento del modelo debe ser reproducible (semilla fija).
5. Cada endpoint documenta su contrato (request/response) en plan.md
   antes de implementarse.
6. El código no se despliega a EC2 si el pipeline de tests falla.
```

### 4.2 `spec.md` — QUÉ y POR QUÉ (sin detalles técnicos)

Pídele al agente que la redacte siguiendo esta estructura:

- **Contexto del problema**: por qué predecir visitantes ayuda a la gestión del atractivo.
- **Usuarios objetivo**: administrador del atractivo, turista, tu docente (evaluador).
- **Historias de usuario** con criterios de aceptación en formato Given/When/Then. Mínimo:
  - *Como administrador, quiero ver el clima actual del lugar para anticipar la afluencia del día.*
  - *Como administrador, quiero una predicción de visitantes para una hora dada, para reforzar personal si se espera alta afluencia.*
  - *Como turista, quiero ver si conviene ir ahora o más tarde según la predicción.*
- **Requisitos funcionales** numerados (RF-1, RF-2...): consultar clima actual, calcular predicción, registrar histórico, listar histórico, (opcional) reentrenar modelo.
- **Requisitos no funcionales**: tiempo de respuesta razonable (<2s incluyendo llamada externa), manejo de caída de la API de clima (no debe tumbar la app), secretos fuera del código.
- **Fuera de alcance**: autenticación de usuarios reales, multi-idioma, notificaciones push (defínelo explícitamente para que el agente no se desvíe).

### 4.3 `plan.md` — CÓMO (arquitectura técnica)

Debe cubrir, como mínimo:

- **Modelo de datos** (tabla `historico_visitas`):

| Campo | Tipo | Nota |
|---|---|---|
| `id` | int, PK | |
| `fecha` | date | |
| `hora` | int (0-23) | |
| `temperatura_c` | float | |
| `condicion_clima` | str | `despejado` / `nublado` / `lluvia_ligera` / `lluvia_fuerte` |
| `es_fin_de_semana` | bool | |
| `visitantes` | int | variable objetivo |

- **Contratos de API**:

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/clima/actual` | GET | Clima actual de la catarata (proxy a OpenWeatherMap) |
| `/api/prediccion` | GET | Predicción de visitantes; parámetro opcional `hora` (default: hora actual) |
| `/api/historico` | GET | Lista paginada del histórico |
| `/api/historico` | POST | Agrega un registro histórico (para poblar/ajustar datos) |
| `/health` | GET | Health check para EC2/monitoreo |

- **Features del modelo**: hora (o franja: mañana/mediodía/tarde), temperatura, condición de clima (one-hot), fin de semana. Documenta por qué eliges cada una.
- **Decisiones descartadas**: por ejemplo, por qué SQLite y no Postgres desde el inicio; por qué regresión lineal y no un modelo más pesado.

### 4.4 `tasks.md` — desglose en tareas verificables

Cada tarea debe ser pequeña, testeable de forma independiente y marcable con checkbox. Ejemplo de arranque:

```markdown
- [ ] T1: Configurar proyecto FastAPI + estructura de carpetas
- [ ] T2: Modelo SQLAlchemy + conexión SQLite
- [ ] T3: Script seed_data.py con datos sintéticos de histórico
- [ ] T4: Cliente de OpenWeatherMap (weather_client.py) + test con mock
- [ ] T5: Endpoint GET /api/clima/actual + test de integración
- [ ] T6: Script train_model.py (entrena y guarda model.pkl)
- [ ] T7: Módulo prediction.py (carga modelo, calcula predicción) + tests unitarios
- [ ] T8: Endpoint GET /api/prediccion + test de integración
- [ ] T9: Endpoints GET/POST /api/historico + tests
- [ ] T10: Frontend simple (dashboard) consumiendo la API
- [ ] T11: Dockerfile/servicio systemd + documentación de despliegue
- [ ] T12: Workflow de GitHub Actions (test + deploy)
```

---

## 5. Dataset histórico (sintético)

Como no hay datos reales, genera un dataset **sintético pero plausible**: una curva base de visitantes por hora (campana centrada al mediodía), reducida por lluvia, aumentada en fin de semana, más ruido aleatorio.

```python
# backend/ml/seed_data.py
import random
from datetime import date, timedelta

CONDICIONES = ["despejado", "nublado", "lluvia_ligera", "lluvia_fuerte"]
MULTIPLICADOR_CLIMA = {
    "despejado": 1.0,
    "nublado": 0.85,
    "lluvia_ligera": 0.5,
    "lluvia_fuerte": 0.15,
}

def curva_base_por_hora(hora: int) -> float:
    # Campana simple centrada en el mediodía, horario 6-18h
    if hora < 6 or hora > 18:
        return 0
    pico = 12
    return max(0, 40 - abs(hora - pico) * 5)

def generar_registro(fecha: date, hora: int) -> dict:
    condicion = random.choices(CONDICIONES, weights=[0.45, 0.30, 0.18, 0.07])[0]
    temperatura = round(random.uniform(18, 30), 1)
    es_finde = fecha.weekday() >= 5
    base = curva_base_por_hora(hora) * MULTIPLICADOR_CLIMA[condicion]
    base *= 1.4 if es_finde else 1.0
    ruido = random.uniform(0.8, 1.2)
    visitantes = max(0, round(base * ruido))
    return {
        "fecha": fecha.isoformat(),
        "hora": hora,
        "temperatura_c": temperatura,
        "condicion_clima": condicion,
        "es_fin_de_semana": es_finde,
        "visitantes": visitantes,
    }

# Genera ~1 año de datos, cada 2 horas dentro del horario de atención
if __name__ == "__main__":
    inicio = date.today() - timedelta(days=365)
    registros = [
        generar_registro(inicio + timedelta(days=d), h)
        for d in range(365)
        for h in range(6, 19, 2)
    ]
    # Insertar `registros` en SQLite vía SQLAlchemy aquí
```

Dile al agente que use esta lógica como base, pero que la implemente contra el modelo SQLAlchemy real (no como código suelto).

---

## 6. Estrategia de testing

- **Unitarios** (`test_prediction.py`): dado clima+hora, la predicción cae en un rango razonable; clima extremo (`lluvia_fuerte`) da predicción menor que `despejado` a igual hora; hora fuera de horario da 0 o un valor mínimo definido.
- **Integración** (`test_api.py`): cada endpoint con `TestClient`, incluyendo el caso en que la API de OpenWeatherMap falla (usa `unittest.mock` o `responses` para simularlo — **nunca** llames a la API real en tests).
- **Fixture de base de datos**: SQLite en memoria (`sqlite:///:memory:`) por test, para no ensuciar el `.db` real.
- **Comando estándar**: `pytest --cov=app --cov-report=term-missing`
- El pipeline de GitHub Actions **no debe desplegar** si algún test falla (ver Sección 8).

---

## 7. Despliegue en AWS EC2

1. **Security Group**: abre el puerto `8000` (o el que uses) entrante desde `0.0.0.0/0` para la demo — para producción real se restringiría, pero para el curso está bien.
2. **En la instancia** (SSH):
   ```bash
   sudo apt update && sudo apt install -y python3.11-venv git
   git clone <tu-repo> catarata-golondrinas
   cd catarata-golondrinas/backend
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # y completa la API key real
   ```
3. **Servicio systemd** (`/etc/systemd/system/catarata-app.service`):
   ```ini
   [Unit]
   Description=Catarata Las Golondrinas API
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/catarata-golondrinas/backend
   EnvironmentFile=/home/ubuntu/catarata-golondrinas/backend/.env
   ExecStart=/home/ubuntu/catarata-golondrinas/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl enable --now catarata-app
   ```
4. Verifica en `http://<IP-PUBLICA-EC2>:8000/docs` (Swagger UI de FastAPI).

---

## 8. GitHub Actions — CI/CD

`.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD - Catarata las Golondrinas

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Instalar dependencias
        run: pip install -r backend/requirements.txt
      - name: Ejecutar tests
        run: pytest backend/tests --cov=backend/app --cov-report=term-missing

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Desplegar en EC2 vía SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ubuntu/catarata-golondrinas
            git pull origin main
            cd backend
            source .venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart catarata-app
```

**Secrets a configurar en GitHub** (`Settings → Secrets and variables → Actions`):
`EC2_HOST`, `EC2_USER` (normalmente `ubuntu`), `EC2_SSH_KEY` (la `.pem` completa), y `OPENWEATHER_API_KEY` (si prefieres inyectarla en vez de tenerla ya en el `.env` del servidor).

---

## 9. Prompt para pegar en OpenCode

Copia todo el bloque de abajo como tu **primer mensaje** en OpenCode, en **modo Plan** (ver Sección 10):

```
Contexto del proyecto:

Estoy construyendo una app en la nube para el curso "Desarrollo de
Aplicaciones para la Nube". El atractivo turístico asignado es
"Catarata las Golondrinas" (Huánuco, Perú, cerca de Tingo María).

Objetivo: la app consulta el clima actual del lugar (temperatura y
condición) vía una API externa, y combinando ese clima con la hora
del día, predice cuántos visitantes se esperan, entrenando un modelo
de regresión (scikit-learn) sobre un histórico de visitantes por
día/hora/temperatura/clima.

Stack ya decidido (no lo cambies sin discutirlo conmigo):
- Backend: FastAPI (Python 3.11+)
- Base de datos: SQLite vía SQLAlchemy
- Predicción: scikit-learn, regresión sobre hora/temperatura/clima/
  fin de semana
- Clima externo: OpenWeatherMap API (API key en .env, nunca
  hardcodeada ni commiteada)
- Frontend: HTML/CSS/JS simple servido como estáticos por FastAPI
- Testing: pytest + TestClient de FastAPI, con mocks para la API de
  clima (nunca llamar a la API real en tests)
- Despliegue objetivo: AWS EC2 vía systemd (sin Docker por ahora)
- CI/CD objetivo: GitHub Actions (job de tests + job de deploy por
  SSH, el deploy solo corre si los tests pasan)

Ubicación de referencia (ajustar si tengo coordenadas más precisas):
lat -9.2957, lon -75.9975 (Tingo María).

Quiero trabajar con metodología Spec-Driven Development. Antes de
escribir una sola línea de código de la aplicación, quiero que
generes, EN ESTE ORDEN, y que me pidas revisión entre cada uno:

1. specs/constitution.md — principios del proyecto (tests
   obligatorios por endpoint, secretos nunca commiteados, modelo
   reproducible con semilla fija, etc.)
2. specs/001-prediccion-visitantes/spec.md — el QUÉ y el POR QUÉ:
   historias de usuario con criterios de aceptación, requisitos
   funcionales numerados, requisitos no funcionales, y qué queda
   fuera de alcance. Sin detalles de implementación todavía.
3. specs/001-prediccion-visitantes/plan.md — el CÓMO: modelo de
   datos (tabla de histórico de visitas), contrato de cada endpoint
   de la API, features del modelo de predicción, decisiones técnicas
   y alternativas descartadas.
4. specs/001-prediccion-visitantes/tasks.md — desglose en tareas
   pequeñas, ordenadas y verificables de forma independiente
   (incluyendo, para cada tarea de lógica, su test correspondiente).

No implementes nada todavía. Genera estos 4 archivos, muéstrame el
contenido, y espera mi aprobación explícita antes de pasar a la
implementación. Si algo del contexto es ambiguo, pregúntame antes de
asumir.
```

Cuando apruebes los 4 archivos, cambia a **modo Build** y pide implementación **tarea por tarea** (no todo de golpe), corriendo los tests después de cada tarea antes de seguir con la siguiente.

---

## 10. ¿Modo Plan o modo Build?

**Empieza en modo Plan.** En OpenCode, Plan es de solo lectura/propuesta: el agente puede razonar, leer el repo y redactar archivos como texto para tu revisión, pero no edita el proyecto todavía. Build sí escribe y ejecuta.

Secuencia recomendada:

1. **Modo Plan** → pega el prompt de la Sección 9 → revisas y ajustas `constitution.md`, `spec.md`, `plan.md`, `tasks.md` hasta que reflejen exactamente lo que quieres. Esta fase es barata de corregir; corregir código ya escrito es más caro.
2. Cuando los 4 archivos te convencen, presiona **Tab** para pasar a **modo Build**.
3. Pide implementación **por tarea** (T1, T2, T3... de `tasks.md`), no todo el proyecto de una vez — así puedes revisar diffs pequeños y correr tests incrementalmente.
4. Si en algún punto el alcance cambia (tu docente pide algo nuevo, encuentras un problema de diseño), vuelve a **Plan** para actualizar `plan.md`/`tasks.md` antes de seguir escribiendo código. No parchees la arquitectura desde Build.
5. Antes de cada `git push` a `main`, corre `pytest` localmente — así no gastas minutos de GitHub Actions en fallos obvios.

---

## Notas finales

- Los puntos marcados ⚠️ CONFIRMAR (Sección 3) son los únicos donde inventé un valor razonable en lugar de preguntarte — ajústalos con lo que sabes del lugar real.
- Si tu docente pide explícitamente Docker o un modelo de ML más robusto (Random Forest, por ejemplo), es un cambio de una sola línea en `plan.md`, no reescribas el resto.
