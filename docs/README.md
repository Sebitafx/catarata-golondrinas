# 🎬 Evidencia en producción (video del docente)

Esta carpeta es donde se sube el video que pidió el docente **después del deploy a la nube**.

## Qué debe mostrar el video

1. Un cambio pequeño y visible (ej. texto del dashboard o estilo del clima).
2. `git add + commit + push` a `main` desde tu PC.
3. La pestaña **Actions** del repo en verde (`test` → `deploy`).
4. La app respondiendo en producción: `http://<IP-PUBLICA-EC2>:8000/` y `/docs` y `/health`.

## Dónde ponerlo

- Opción A (recomendada): súbelo a YouTube (no listado) y pega aquí el enlace.
- Opción B: guarda el archivo como `docs/video-produccion.mp4` (si pesa >100 MB GitHub lo rechaza — usa la opción A).

## Plantilla para completar

- Fecha del deploy: 2026-09-25
- Commit del cambio: `bac4f1c` (badge En vivo 🟢 + footer v1.1)
- Run de Actions en verde: run #5 `success` (test + deploy)
- URL producción: `http://3.148.214.177:8000/`
- Enlace video: [`video-produccion.mp4`](./video-produccion.mp4) (55 MB, en esta carpeta)

> Estado actual: ✅ en producción (systemd activo, pipeline verde).
