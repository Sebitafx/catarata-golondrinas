from unittest.mock import AsyncMock, patch


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_clima_200(client):
    fake = {"temperatura_c": 26.4, "condicion": "nublado", "descripcion": "nubes",
            "humedad": 78, "hora_consulta": "2026-09-25T15:00:00-05:00",
            "fuente": "openweathermap", "lat": -8.7938, "lon": -76.3348}
    with patch("app.main.get_actual", new=AsyncMock(return_value=fake)):
        r = client.get("/api/clima/actual")
        assert r.status_code == 200
        assert r.json()["condicion"] == "nublado"


def test_clima_503_y_health_sigue(client):
    from app.weather_client import WeatherServiceError
    with patch("app.main.get_actual", side_effect=WeatherServiceError("caído")):
        r = client.get("/api/clima/actual")
        assert r.status_code == 503
    assert client.get("/health").status_code == 200


def test_prediccion_200_y_fuera_horario(client):
    fake = {"temperatura_c": 27.0, "condicion": "despejado", "descripcion": "sol",
            "humedad": 60, "hora_consulta": "2026-09-25T12:00:00-05:00",
            "fuente": "openweathermap", "lat": -8.7938, "lon": -76.3348}
    with patch("app.main.get_actual", new=AsyncMock(return_value=fake)):
        with patch("app.main.pred_mod.predict", return_value=35) as m:
            r = client.get("/api/prediccion?hora=12&fecha=2026-09-27")
            assert r.status_code == 200
            assert r.json()["visitantes_estimados"] == 35
        r2 = client.get("/api/prediccion?hora=3&fecha=2026-09-27")
        assert r2.status_code == 200
        assert r2.json()["visitantes_estimados"] == 0
        assert "fuera de horario" in r2.json()["nota"]


def test_pronostico_200_y_503(client):
    fake = {"fuente": "openweathermap", "bloques": [
        {"hora_consulta": "2026-09-25 18:00:00", "temperatura_c": 27.1, "condicion": "lluvia_ligera", "descripcion": "lluvia ligera", "humedad": 80},
        {"hora_consulta": "2026-09-25 21:00:00", "temperatura_c": 24.3, "condicion": "nublado", "descripcion": "nublado", "humedad": 88}]}
    with patch("app.main.get_pronostico", new=AsyncMock(return_value=fake)):
        r = client.get("/api/clima/pronostico?horas=2")
        assert r.status_code == 200
        assert len(r.json()["bloques"]) == 2
    from app.weather_client import WeatherServiceError
    with patch("app.main.get_pronostico", side_effect=WeatherServiceError("caído")):
        assert client.get("/api/clima/pronostico").status_code == 503


def test_historico_crud_401_201_422(client):
    # sin key -> 401
    r = client.post("/api/historico", json={"fecha": "2026-09-25", "hora": 12, "temperatura_c": 27.0,
                                            "condicion_clima": "despejado", "es_fin_de_semana": False, "visitantes": 20})
    assert r.status_code == 401
    # con key -> 201
    r = client.post("/api/historico", headers={"X-Admin-Key": "test-admin-key"},
                    json={"fecha": "2026-09-25", "hora": 12, "temperatura_c": 27.0,
                          "condicion_clima": "despejado", "es_fin_de_semana": False, "visitantes": 20})
    assert r.status_code == 201, r.text
    # inválido -> 422
    r = client.post("/api/historico", headers={"X-Admin-Key": "test-admin-key"},
                    json={"fecha": "2026-09-25", "hora": 99, "temperatura_c": 27.0,
                          "condicion_clima": "mal", "es_fin_de_semana": False, "visitantes": -1})
    assert r.status_code == 422
    # get público paginado
    r = client.get("/api/historico?page=1&size=5")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_root_200(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    txt = r.text
    assert 'id="clima"' in txt and 'id="prediccion"' in txt
    assert 'id="btn-predecir"' in txt and 'id="ficha-lugar"' in txt
