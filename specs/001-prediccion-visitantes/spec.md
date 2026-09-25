# SPEC 001 — Predicción de visitantes según clima y hora

> Atractivo: Catarata Las Golondrinas — Caserío Río Tigre, distrito Mariano Dámaso Beraún, provincia Leoncio Prado, Huánuco, Perú.
> Acceso: 20 min en carro desde Tingo María + 8 min caminata por bosque.
> Altitud ~1022 msnm, caída ~15 m.
> Estado: `spec` (QUÉ y POR QUÉ). Sin detalles de implementación — ver `plan.md` para el CÓMO.

---

## 1. Contexto del problema

La visita a la catarata depende fuertemente del clima (lluvia en selva alta) y de la hora del día. El administrador no tiene forma de anticipar afluencia para reforzar personal, limpieza o seguridad en la poza pequeña. El turista no sabe si conviene ir ahora o más tarde.

La app resuelve esto consultando el clima actual del lugar y combinándolo con la hora para predecir visitantes esperados, entrenando una regresión sobre un histórico (día/hora/temperatura/clima).

## 2. Supuestos de dominio (fuente explícita)

| ID | Supuesto | Valor | Fuente |
|----|----------|-------|--------|
| S-1 | Coordenadas | lat `-8.7938`, lon `-76.3348` | Usuario, aprox. Río Tigre |
| S-2 | Horario atención | `08:00–18:00` | Experiencia en sitio: a las 18:00 ya no había nadie |
| S-3 | Aforo práctico tope | `40` personas simultáneas | Observación sitio + reseñas Google Maps (poza/explanada pequeña, con >30-40 se vuelve incómodo). Sin valor oficial MINCETUR |
| S-4 | Clima externo | OpenWeatherMap Current Weather | API key propia en `.env`, nunca commiteada |
| S-5 | Histórico inicial | Sintético ~1 año, cada 2h en 08-18h (8,10,12,14,16,18 → 6 franjas/día → ~2190 registros) | No hay datos reales; generador con semilla fija |
| S-6 | Protección escritura | `POST /api/historico` exige `X-Admin-Key`; lecturas públicas sin login | Decisión negocio: anti-vandalismo mínimo sin fricción turista |

Cambio de cualquier S-* obliga a actualizar este spec primero (C8 constitución).

## 3. Usuarios objetivo

- **U1 Administrador del atractivo:** anticipa afluencia del día, decide personal.
- **U2 Turista:** decide si ir ahora o más tarde.
- **U3 Docente evaluador:** verifica specs, tests, Swagger `/docs`, pipeline verde, app en EC2.

## 4. Historias de usuario (Given/When/Then)

### HU-1 — Ver clima actual y pronóstico del lugar
> Como administrador, quiero ver el clima actual y el pronóstico de las próximas horas para anticipar la afluencia del día.

- **Given** la app está desplegada y hay API key válida
- **When** consulto `GET /api/clima/actual` y `GET /api/clima/pronostico`
- **Then** recibo `temperatura_c`, `condicion` normalizada, `hora_consulta` y `fuente`, en <2s (actual) / <3s (pronóstico)
- **Y** el pronóstico usa la **misma API y key** (OpenWeather `forecast` 3h/5días, sin servicio nuevo) con 8 bloques (~24h)
- **Y** si OpenWeather cae, recibo `503` con mensaje claro y la app sigue viva (`/health` en 200)

### HU-2 — Predecir visitantes por hora
> Como administrador, quiero una predicción de visitantes para una hora dada, para reforzar personal si se espera alta afluencia.

- **Given** hay modelo entrenado y clima actual disponible
- **When** consulto `GET /api/prediccion?hora=12`
- **Then** recibo `visitantes_estimados` entre `0` y `40`, más `hora`, `clima_usado`, `es_fin_de_semana`
- **Y** si `hora <8 o hora >18` recibo `0` con `nota: fuera de horario`
- **Y** `lluvia_fuerte` siempre predice menos que `despejado` a igual hora

### HU-3 — Decidir mejor momento para ir
> Como turista, quiero ver si conviene ir ahora o más tarde según la predicción.

- **Given** abro el dashboard `/`
- **When** la página carga
- **Then** veo ficha del lugar (ubicación Río Tigre, alt 1022msnm, caída 15m, acceso 20min+8min, horario 08-18, aforo 40) + hora actual Lima en vivo + clima actual + predicción hora actual
- **Y** con selector `hora` (fecha auto = hoy Lima, no se pide fecha pasada) y botón `Predecir afluencia` veo predicción buscada con barra `x/40`
- **Y** veo próximas 3 franjas (+2h/+4h/+6h) y últimos históricos, sin necesidad de saber usar la API ni registrarme

### HU-4 — Registrar histórico protegido (base del modelo)
> Como administrador, quiero agregar histórico con clave simple para corregir el modelo sin exponerlo al vandalismo.

- **Given** endpoint de escritura protegido con `X-Admin-Key` (sin registro/JWT en v1)
- **When** hago `POST /api/historico` con `X-Admin-Key` válida y registro válido
- **Then** queda persistido y visible en `GET /api/historico?page=1`
- **Y** sin header o con clave inválida recibo `401` y nada se persiste

## 5. Requisitos funcionales

| ID | Requisito | Historia | Verificado por |
|----|-----------|----------|----------------|
| RF-1 | Consultar clima actual: `GET /api/clima/actual` proxy a OpenWeather, normaliza a `despejado/nublado/lluvia_ligera/lluvia_fuerte` | HU-1 | test_api clima 200 + mock |
| RF-7 | Pronóstico clima 24h (misma API/key, sin servicio nuevo): `GET /api/clima/pronostico?horas=8` proxy a OpenWeather `forecast`, normalizado por bloque 3h | HU-1 | test_api pronostico 200/503 + mock |
| RF-2 | Calcular predicción: `GET /api/prediccion?hora&fecha(optional)` combina clima + hora + finde con modelo sklearn | HU-2 | test_prediction + test_api prediccion |
| RF-3 | Registrar histórico protegido: `POST /api/historico` exige `X-Admin-Key`, valida `hora 0-23`, `temperatura`, `condicion` enum, `visitantes >=0`; `401` sin/inválida, `422` datos mal | HU-4 | test_api post 201 / 401 / 422 |
| RF-4 | Listar histórico paginado público: `GET /api/historico?page&size` sin login | HU-4 | test_api get paginado |
| RF-5 | Dashboard `/` público sin login, **modo oscuro por defecto** (toggle a claro), con ficha lugar + **fotos reales** `lugar-catarata.jpg/lugar-poza.jpg` + hora Lima en vivo + clima + predicción con selector solo `hora` (**fecha auto = hoy Lima**, no se predice pasado) + pronóstico 24h + próximas 3 franjas + últimos históricos en **tabla** (no texto corrido), servido como estático por FastAPI | HU-3 | test_api `/` 200 contiene marcadores |
| RF-6 | Health check `GET /health` retorna `{"status":"ok"}` sin depender de OpenWeather ni del modelo | HU-1 | test_api health |

## 6. Requisitos no funcionales

| ID | Requisito | Criterio medible |
|----|-----------|------------------|
| RNF-1 | Latencia | `GET /api/clima/actual` y `/api/prediccion` <2s, `/api/clima/pronostico` <3s con red normal (excluye cold-start EC2) |
| RNF-2 | Resiliencia clima | Si OpenWeather timeout/error → `503` JSON, no tumba proceso; `/health` sigue 200 |
| RNF-3 | Seguridad secretos + escritura | `grep -r API_KEY backend --exclude=.env.example` y `grep -r ADMIN_KEY` no muestran valor real; `.env` en `.gitignore`; `POST` sin key → `401` |
| RNF-8 | UX sin fricción | Dashboard y predicción usables sin cuenta; solo escritura pide clave; botón `Predecir` responde <2s |
| RNF-4 | Reproducibilidad | `RANDOM_SEED=42`; re-seed + re-train da mismo `model.pkl` (hash o RMSE idéntico en test) |
| RNF-5 | Tope razonable | Ninguna predicción >40 ni <0 |
| RNF-6 | Docs automáticas | `/docs` Swagger accesible en local y EC2 |
| RNF-7 | Portabilidad cloud | Corre en EC2 free-tier 1GB con `venv+systemd`, sin Docker obligatorio |

## 7. Fuera de alcance (v1 explícito)

- Login de usuarios reales con registro / JWT / tabla users / recuperación contraseña (v1 usa solo `X-Admin-Key` para escritura, sin cuentas).
- Multi-idioma, notificaciones push, reservas/pagos.
- Mapa en tiempo real, multi-atractivo.
- Reentrenamiento automático en caliente (se reentrena por script manual `train_model.py`).
- Docker obligatorio (opcional solo si el docente lo pide).

## 8. Criterios de aceptación global

- [ ] `pytest` verde local con cobertura visible.
- [ ] `/docs` muestra los 6 endpoints API (health + clima actual + clima pronostico + prediccion + historico GET/POST).
- [ ] Predicción mediodía despejado finde > mañana lluvia fuerte laborable (demo guiada).
- [ ] `GET /api/prediccion?hora=3` → `0` fuera de horario.
- [ ] `POST /api/historico` sin `X-Admin-Key` → `401`, con válida → `201`.
- [ ] Sin `.env` con key real commiteado.
- [ ] App accesible en `http://<IP-EC2>:8000/docs`.

## 9. Riesgos conocidos

- Sin datos reales el modelo solo aprende la función sintética — declararlo en README/defensa, no venderlo como ML productivo.
- OpenWeather free-tier con límites — cachear 10 min en memoria para no exceder cuota (detalle en `plan.md`).
- `sklearn` pesado para 1GB RAM en EC2 — instalar con `--no-cache-dir` + swap si hace falta.
