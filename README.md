# Catarata Las Golondrinas — Predicción de visitantes según clima y hora

Río Tigre, Mariano Dámaso Beraún, Leoncio Prado, Huánuco. Lat -8.7938, Lon -76.3348. Alt 1022 msnm, caída 15 m. Horario 08–18, aforo práctico 40 (sin valor oficial MINCETUR, supuesto por poza pequeña).

## Modelo sintético (declaración honesta)
Sin datos reales, el modelo aprende la función sintética (campana mediodía x clima x finde). Sirve para demo de curso, no como ML productivo.

## Local
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # completa OPENWEATHER_API_KEY y ADMIN_KEY
python -m ml.train_model
uvicorn app.main:app --reload --port 8000
# http://localhost:8000/ y http://localhost:8000/docs
```

## Tests
```bash
pytest backend/tests --cov=backend/app --cov-report=term-missing -v
```

## EC2 (Ubuntu 24.04 t2.micro/t3.micro, Ohio)
SG: 22/tcp + 8000/tcp. Luego:
```bash
sudo apt update && sudo apt install -y python3.11-venv git
git clone <repo> catarata-golondrinas
cd catarata-golondrinas/backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
cp .env.example .env  # edita keys
python -m ml.train_model
sudo cp ../deploy/catarata-app.service /etc/systemd/system/
sudo systemctl enable --now catarata-app
curl http://<IP>:8000/health
```

## Secrets GitHub Actions
`EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `OPENWEATHER_API_KEY`, `ADMIN_KEY`.
