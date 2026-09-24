import os
import json
import math
import time
import threading
import requests
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

USER_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    try:
        with open(USER_FILE, 'w') as f:
            json.dump(users, f)
    except Exception as e:
        print("Error saving users:", e)

users_db = load_users()

def calc_wbgt(t, rh, s, w):
    return 0.567 * t + 0.393 * (rh / 100.0 * 6.105 * math.exp(17.27 * t / (237.7 + t))) + 3.94 + (s / 1000.0) * 1.5 - min(w / 3.6, 4.0) * 0.3

def calc_dist(lat1, lon1, lat2, lon2):
    r = lambda x: x * math.pi / 180
    h = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return round(12742e3 * math.asin(math.sqrt(h)))

def get_nearest_shade(lat, lon):
    try:
        query = f'[out:json][timeout:15];(way["leisure"="park"](around:900,{lat},{lon});node["amenity"="shelter"](around:900,{lat},{lon}););out center 20;'
        resp = requests.post('https://overpass-api.de/api/interpreter', data={'data': query}, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=10)
        data = resp.json()
        elements = []
        for e in data.get('elements', []):
            e_lat = e.get('lat') or e.get('center', {}).get('lat')
            e_lon = e.get('lon') or e.get('center', {}).get('lon')
            if e_lat and e_lon:
                name = e.get('tags', {}).get('name', 'Shaded spot')
                d = calc_dist(lat, lon, e_lat, e_lon)
                elements.append({'name': name, 'd': d})
        elements.sort(key=lambda x: x['d'])
        if elements:
            return f" Nearest shade: {elements[0]['name']}, {elements[0]['d']} m."
        return ""
    except Exception:
        return ""

def check_heat_alerts():
    while True:
        try:
            for token, u in list(users_db.items()):
                try:
                    age = int(u.get('age', 0) or 0)
                    thr = 32 - (2 if (age >= 60 or (0 < age <= 12)) else 0) - (1.5 if len(u.get('cond', [])) > 0 else 0)
                    url = f"https://api.open-meteo.com/v1/forecast?latitude={u['lat']}&longitude={u['lon']}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation&forecast_days=2&timezone=auto"
                    r = requests.get(url, timeout=10).json()
                    
                    utc_off = r.get('utc_offset_seconds', 0)
                    hourly = r.get('hourly', {})
                    times = hourly.get('time', [])
                    temps = hourly.get('temperature_2m', [])
                    rhs = hourly.get('relative_humidity_2m', [])
                    winds = hourly.get('wind_speed_10m', [])
                    rads = hourly.get('shortwave_radiation', [])
                    
                    now_ts = time.time()
                    for i in range(len(times)):
                        w = calc_wbgt(temps[i], rhs[i], rads[i], winds[i])
                        t_str = times[i]
                        dt = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
                        t_ts = dt.timestamp() - utc_off
                        mins = (t_ts - now_ts) / 60.0
                        
                        if w >= thr and -30 < mins <= 15 and u.get('last') != times[i]:
                            shade_str = "" if u.get('shade') is False else get_nearest_shade(u['lat'], u['lon'])
                            level_name = "Extreme" if w >= 32 else "High"
                            payload = {
                                "to": token,
                                "title": f"{level_name} heat in 15 min",
                                "body": f"WBGT ~{w:.1f}°C. Move indoors, drink water.{shade_str}",
                                "sound": "default",
                                "priority": "high",
                                "channelId": "default"
                            }
                            requests.post('https://exp.host/--/api/v2/push/send', json=payload, timeout=10)
                            users_db[token]['last'] = times[i]
                            save_users(users_db)
                            print(f"Alert sent to {token[-8:]} for {times[i]}")
                            break
                except Exception as err:
                    print("User check error:", err)
        except Exception as e:
            print("Global check error:", e)
        time.sleep(600)

threading.Thread(target=check_heat_alerts, daemon=True).start()

@app.route('/', methods=['GET'])
def home():
    return f"CalorPulse server running. Users: {len(users_db)}"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True, silent=True)
    if not data or 'token' not in data:
        return jsonify({'error': 'bad request'}), 400
    token = data['token']
    users_db[token] = {**users_db.get(token, {}), **data}
    save_users(users_db)
    return 'ok'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
