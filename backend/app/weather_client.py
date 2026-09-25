import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import httpx

LAT = float(os.getenv("LAT", "-8.7938"))
LON = float(os.getenv("LON", "-76.3348"))

_CACHE: dict = {"data": None, "ts": 0.0}
TTL = 600  # 10 min RNF-2 / ahorro cuota free-tier


class WeatherServiceError(Exception):
    pass


def mapear_condicion(main: str, rain_mm: float = 0.0) -> str:
    m = (main or "").lower()
    if m == "clear":
        return "despejado"
    if m == "clouds":
        return "nublado"
    if m == "drizzle":
        return "lluvia_ligera"
    if m in ("thunderstorm",):
        return "lluvia_fuerte"
    if m == "rain":
        return "lluvia_fuerte" if rain_mm > 2.5 else "lluvia_ligera"
    if m in ("snow", "mist", "fog", "haze"):
        return "nublado"
    return "nublado"


async def get_actual() -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        raise WeatherServiceError("falta OPENWEATHER_API_KEY")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": LAT, "lon": LON, "appid": api_key, "units": "metric", "lang": "es"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            j = r.json()
    except Exception as e:
        # fallback a cache si existe
        if _CACHE["data"] is not None and (time.time() - _CACHE["ts"]) < TTL * 6:
            return _CACHE["data"]
        raise WeatherServiceError(f"servicio de clima no disponible: {e}")

    main = (j.get("weather") or [{}])[0].get("main", "")
    desc = (j.get("weather") or [{}])[0].get("description", "")
    rain_mm = float(((j.get("rain") or {}).get("1h")) or 0.0)
    data = {
        "temperatura_c": round(float(j["main"]["temp"]), 1),
        "condicion": mapear_condicion(main, rain_mm),
        "descripcion": desc,
        "humedad": int(j["main"].get("humidity", 0)),
        "hora_consulta": datetime.now(ZoneInfo("America/Lima")).isoformat(),
        "fuente": "openweathermap",
        "lat": LAT,
        "lon": LON,
    }
    _CACHE["data"] = data
    _CACHE["ts"] = time.time()
    return data


async def get_pronostico(horas: int = 8) -> dict:
    """Pronóstico por bloques 3h con la MISMA api/key (OpenWeather forecast, gratis).
    Sin servicio nuevo. `horas` = nº bloques (1-8 ≈ 24h)."""
    n = max(1, min(8, int(horas)))
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        raise WeatherServiceError("falta OPENWEATHER_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": LAT, "lon": LON, "appid": api_key, "units": "metric", "lang": "es", "cnt": n}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            j = r.json()
    except Exception as e:
        raise WeatherServiceError(f"servicio de clima no disponible: {e}")
    bloques = []
    for item in (j.get("list") or [])[:n]:
        main = (item.get("weather") or [{}])[0].get("main", "")
        desc = (item.get("weather") or [{}])[0].get("description", "")
        rain_mm = float(((item.get("rain") or {}).get("3h")) or 0.0)
        bloques.append({
            "hora_consulta": item.get("dt_txt", ""),
            "temperatura_c": round(float(item["main"]["temp"]), 1),
            "condicion": mapear_condicion(main, rain_mm),
            "descripcion": desc,
            "humedad": int(item["main"].get("humidity", 0)),
        })
    return {"fuente": "openweathermap", "bloques": bloques}
