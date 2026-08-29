import httpx

BASELINES = {
    "banana": {"storage_temp_c": "12-14", "relative_humidity_pct": "85-95", "note": "Project reference baseline; verify against your experimental protocol."},
    "apple": {"storage_temp_c": "0-4", "relative_humidity_pct": "90-95", "note": "Project reference baseline; verify against your experimental protocol."},
    "mango": {"storage_temp_c": "10-13", "relative_humidity_pct": "85-90", "note": "Project reference baseline; verify against your experimental protocol."},
    "orange": {"storage_temp_c": "3-9", "relative_humidity_pct": "85-90", "note": "Project reference baseline; verify against your experimental protocol."},
}

async def external_context(fruit_type: str, lat: float | None, lon: float | None) -> dict:
    data = {"baseline": BASELINES.get(fruit_type.lower(), {"note": "No fruit-specific baseline configured yet."}), "weather": None}
    if lat is None or lon is None:
        return data
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m", "timezone": "auto"}
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            current = response.json().get("current", {})
            data["weather"] = {
                "temperature_c": current.get("temperature_2m"),
                "humidity_pct": current.get("relative_humidity_2m"),
                "source": "Open-Meteo",
            }
    except Exception as exc:
        data["weather_error"] = str(exc)
    return data
