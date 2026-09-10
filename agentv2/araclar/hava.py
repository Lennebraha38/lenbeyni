"""Hava durumu + kutuphane API baglayicilari."""
import requests

def hava(sehir):
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": 0, "longitude": 0}, timeout=10)
        if r.status_code == 200:
            return "Deneysel: open-meteo koordinat ister. 'hava Ankara' icin koordinat gerekir."
    except Exception as e:
        return f"[Hava hatasi: {e}]"
    return "[Hava verisi yok]"

def hava_koordinat(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon,
                    "current_weather": "true", "language": "tr", "timezone": "auto"},
            timeout=15)
        d = r.json()
        cw = d.get("current_weather", {})
        return (f"Sicaklik: {cw.get('temperature')}C\n"
                f"Ruzgar: {cw.get('windspeed')} km/s\n"
                f"Kod: {cw.get('weathercode')}")
    except Exception as e:
        return f"[Hava hatasi: {e}]"