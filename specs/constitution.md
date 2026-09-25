# Constitución del proyecto — Catarata Las Golondrinas

> Curso: Desarrollo de Aplicaciones para la Nube
> Atractivo: Catarata Las Golondrinas, Caserío Río Tigre, Mariano Dámaso Beraún, Leoncio Prado, Huánuco, Perú.
> Coordenadas referencia: lat `-8.7938`, lon `-76.3348` / Alt 1022 msnm / Caída ~15 m.
> Horario supuesto validado en sitio: `08:00–18:00` / Aforo práctico tope: `40 personas` (sin valor oficial MINCETUR).
> Metodología: Spec-Driven Development. Este archivo es norma superior. Si `spec.md`, `plan.md` o código lo contradicen, se corrige el nivel inferior.

---

## C1. Tests obligatorios por endpoint público

Todo endpoint público (`/api/*`, `/health`, `/`) debe tener al menos un test de integración con `TestClient` antes de considerarse terminado.

Racional: es la evidencia principal para CI/CD y para evaluación docente.

## C2. Lógica de predicción con tests unitarios y casos borde

`prediction.py` debe cubrir:

- `lluvia_fuerte` < `despejado` a igual hora/temperatura.
- Hora fuera de `08–18` → `0` (cerrado, sin excepción).
- Sin datos históricos / sin `model.pkl` → error controlado, no crash.
- Predicción siempre `0 <= valor <= 40` (tope aforo práctico).

## C3. Ningún secreto se commitea + escritura protegida mínima

API keys, `.pem`, `ADMIN_KEY`, credenciales: nunca en git, nunca hardcodeadas.

- Local: `.env` (no versionado).
- Servidor EC2: `.env` + `EnvironmentFile` systemd.
- CI/CD: GitHub Secrets (`EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `OPENWEATHER_API_KEY`, `ADMIN_KEY`).
- Sí se versiona: `.env.example` con claves vacías.
- Lecturas (`GET /api/clima/actual`, `/api/prediccion`, `/api/historico`, `/`, `/health`) son públicas sin login para cero fricción turista.
- Escritura (`POST /api/historico`) exige header `X-Admin-Key == ADMIN_KEY` (comparación constant-time). Sin tabla users, sin JWT, sin registro en v1.

Violación = tarea bloqueada hasta rotar el secreto.

## C4. Reproducibilidad del modelo

- `seed_data.py` y `train_model.py` con semilla fija (`RANDOM_SEED = 42`).
- `model.pkl` no se commitea (generado en build/deploy o por script).
- Re-entrenar con misma semilla + mismo CSV/DB debe dar mismo modelo.

## C5. Contrato antes que código

Ningún endpoint se implementa sin contrato previo en `plan.md`: método, path, query/body params, response JSON con ejemplo, códigos de error.

## C6. No hay deploy si el pipeline falla

- `pytest` local verde antes de cada `push` a `main`.
- GitHub Actions: job `test` → job `deploy` (solo `push` a `main` y solo si `test` pasa).
- En EC2: `systemctl restart` solo después de `git pull + pip install` exitosos.

## C7. Trazabilidad spec → plan → tasks → tests

Cada tarea en `tasks.md` referencia `RF-*` de `spec.md`. Cada `RF-*` tiene al menos un test que lo verifica. Sin RF huérfanos ni tests sin RF.

## C8. Supuestos explícitos, no magia

Todo valor de dominio debe estar documentado como supuesto con fuente:

- `LAT=-8.7938, LON=-76.3348` (aprox. usuario, Río Tigre).
- `HORARIO=08-18` (experiencia en sitio, después no hay nadie).
- `AFORO_MAX=40` (observación Google Maps / sitio, poza pequeña).
- `CURVA_BASE` centrada al mediodía (lógica seed sintético).

Si cambia un supuesto, se actualiza `spec.md` primero, luego `plan.md`.
