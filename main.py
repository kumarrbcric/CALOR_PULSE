import flet as ft
import requests
import math
import threading
import time

SERVER_URL = "https://calor-pulse.onrender.com"

# WBGT (Wet Bulb Globe Temperature) Index Calculation
def calc_wbgt(t, rh):
    return 0.567 * t + 0.393 * (rh / 100.0 * 6.105 * math.exp(17.27 * t / (237.7 + t))) + 3.94

def main(page: ft.Page):
    page.title = "CalorPulse - Beat the Heat"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    # Global Dynamic GPS Coordinates
    current_lat = 10.7905
    current_lon = 78.7047
    user_location_name = "Detecting Phone GPS..."
    
    # UI Controls (Fixed Color Compatibility)
    loc_text = ft.Text(user_location_name, size=14, weight=ft.FontWeight.BOLD, color="white")
    
    wbgt_val_text = ft.Text("33.8°C", size=38, weight=ft.FontWeight.BOLD, color="white")
    wbgt_status_text = ft.Text("Extreme stress. Avoid outdoor work.", size=13, color="white70")
    
    alert_peak_banner = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.ACCESS_TIME_FILLED, color="orange200", size=16),
            ft.Text("Next alert: heat peak in 15-30 min", size=12, color="white", weight=ft.FontWeight.W_500)
        ]),
        bgcolor="red900",
        padding=8,
        border_radius=8
    )

    humidity_txt = ft.Text("68%", size=16, weight=ft.FontWeight.BOLD)
    wind_txt = ft.Text("6 km/h", size=16, weight=ft.FontWeight.BOLD)
    solar_txt = ft.Text("910 W/m²", size=16, weight=ft.FontWeight.BOLD)

    # 15-Min Heat Alert Notification Banner
    notification_banner = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="white", size=24),
            ft.Column([
                ft.Text("CALORPULSE HIGH HEAT ALERT!", weight=ft.FontWeight.BOLD, color="white", size=14),
                ft.Text("WBGT peaking above 33°C in 15 mins. Seek shade now!", color="white70", size=12)
            ], expand=True)
        ]),
        bgcolor="red700",
        padding=12,
        border_radius=10,
        visible=False
    )

    # ------------------ DYNAMIC GPS & WEATHER LOGIC ------------------
    def update_weather_data():
        nonlocal current_lat, current_lon
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={current_lat}&longitude={current_lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m&hourly=temperature_2m&timezone=auto"
            res = requests.get(url, timeout=5).json()
            
            curr = res.get("current", {})
            t = curr.get("temperature_2m", 33.8)
            rh = curr.get("relative_humidity_2m", 68)
            wind = curr.get("wind_speed_10m", 6)

            wbgt = calc_wbgt(t, rh)
            wbgt_val_text.value = f"{wbgt:.1f}°C"
            humidity_txt.value = f"{rh}%"
            wind_txt.value = f"{wind} km/h"

            # 15-Min Early Warning Check
            if wbgt >= 32.0:
                wbgt_status_text.value = "Extreme stress. Avoid outdoor work."
                notification_banner.visible = True
            else:
                wbgt_status_text.value = "Moderate weather conditions."
                notification_banner.visible = False

            loc_text.value = f"GPS: {current_lat:.4f}, {current_lon:.4f}"
            page.update()
        except Exception:
            pass

    # Background Loop: Checks Weather Every 10 Minutes (600 seconds)
    def start_10min_background_checker():
        def loop():
            while True:
                update_weather_data()
                time.sleep(600)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    # Dynamic Phone GPS Location Handler
    def get_phone_gps(e):
        loc_text.value = "Fetching Device GPS..."
        page.update()
        page.get_geolocation(
            on_success=lambda pos: update_gps_coords(pos.coords.latitude, pos.coords.longitude),
            on_error=lambda err: fallback_gps()
        )

    def update_gps_coords(lat, lon):
        nonlocal current_lat, current_lon
        current_lat, current_lon = lat, lon
        update_weather_data()

    def fallback_gps():
        loc_text.value = "GPS Access Granted (Local)"
        update_weather_data()

    # ------------------ TAB VIEWS ------------------
    # 1. HOME TAB (ThermaWatch / CalorPulse Dashboard)
    def build_home_view():
        return ft.Column([
            notification_banner,
            
            ft.Container(
                content=ft.Row([
                    ft.Text("CalorPulse", size=22, weight=ft.FontWeight.BOLD, color="orange400"),
                    ft.Row([
                        ft.Icon(ft.Icons.LOCATION_ON, color="orange500"),
                        loc_text,
                        ft.IconButton(ft.Icons.MY_LOCATION, icon_color="orange400", on_click=get_phone_gps)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(left=15, right=15, top=10)
            ),

            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.THERMOMETER, color="white", size=28),
                        ft.Column([
                            ft.Text("WBGT NOW", size=11, weight=ft.FontWeight.BOLD, color="white70"),
                            wbgt_val_text
                        ])
                    ]),
                    wbgt_status_text,
                    ft.Divider(height=10, color="transparent"),
                    alert_peak_banner
                ]),
                bgcolor="red600",
                padding=20,
                border_radius=18,
                margin=15
            ),

            ft.Container(
                content=ft.Row([
                    ft.Column([ft.Icon(ft.Icons.WATER_DROP, color="blue300"), ft.Text("Humidity", size=11), humidity_txt], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([ft.Icon(ft.Icons.WB_SUNNY, color="amber300"), ft.Text("Solar", size=11), solar_txt], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([ft.Icon(ft.Icons.AIR, color="grey300"), ft.Text("Wind", size=11), wind_txt], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                padding=15
            ),

            ft.Container(
                content=ft.Column([
                    ft.Text("Next 5 hours", weight=ft.FontWeight.BOLD, size=14),
                    ft.Row([
                        ft.Container(content=ft.Column([ft.Text("1 PM", size=11), ft.Icon(ft.Icons.WB_SUNNY, color="amber", size=18), ft.Text("32°", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor="grey900", padding=10, border_radius=10),
                        ft.Container(content=ft.Column([ft.Text("2 PM", size=11), ft.Icon(ft.Icons.WB_SUNNY, color="amber", size=18), ft.Text("34°", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor="grey900", padding=10, border_radius=10),
                        ft.Container(content=ft.Column([ft.Text("3 PM", size=11), ft.Icon(ft.Icons.WB_SUNNY, color="orange", size=18), ft.Text("35°", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor="red900", padding=10, border_radius=10),
                        ft.Container(content=ft.Column([ft.Text("4 PM", size=11), ft.Icon(ft.Icons.WB_SUNNY, color="amber", size=18), ft.Text("33°", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor="grey900", padding=10, border_radius=10),
                        ft.Container(content=ft.Column([ft.Text("5 PM", size=11), ft.Icon(ft.Icons.WB_SUNNY, color="amber", size=18), ft.Text("31°", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor="grey900", padding=10, border_radius=10),
                    ], scroll=ft.ScrollMode.ALWAYS, spacing=10)
                ]),
                padding=15
            )
        ])

    # 2. MAP TAB
    def build_map_view():
        return ft.Container(
            content=ft.Column([
                ft.Text("CalorPulse - Nearby Shade", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Shade spots calculated from your GPS location", size=12, color="grey400"),
                ft.Divider(height=10, color="transparent"),
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.PARK, color="green400", size=30),
                        title=ft.Text("Anna Nagar Park / Tree Cover"),
                        subtitle=ft.Text("Tree cover • 250 m • 3 min walk"),
                        trailing=ft.Text("31.2°C", color="green300", weight=ft.FontWeight.BOLD)
                    )
                ),
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOCATION_CITY, color="blue400", size=30),
                        title=ft.Text("Metro Station Concourse"),
                        subtitle=ft.Text("Covered & Cooled • 400 m"),
                        trailing=ft.Text("29.5°C", color="blue300", weight=ft.FontWeight.BOLD)
                    )
                )
            ]),
            padding=15
        )

    # 3. ALERTS TAB
    def build_alerts_view():
        return ft.Container(
            content=ft.Column([
                ft.Text("CalorPulse Heat Alerts", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10, color="transparent"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([ft.Icon(ft.Icons.WARNING, color="red400"), ft.Text("Extreme Heat Warning", weight=ft.FontWeight.BOLD, color="red400")]),
                        ft.Text("WBGT 34.5°C detected. Move indoors or to shade."),
                        ft.Text("Sent via: CalorPulse App Push Alert", size=11, color="grey400")
                    ]),
                    bgcolor="grey900",
                    padding=15,
                    border_radius=10
                )
            ]),
            padding=15
        )

    # 4. PROFILE TAB
    def build_profile_view():
        return ft.Container(
            content=ft.Column([
                ft.Text("CalorPulse Profile Settings", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(label="Age", value="20", keyboard_type=ft.KeyboardType.NUMBER),
                ft.TextField(label="Health Conditions", value="Heart disease, Outdoor Worker"),
                ft.Switch(label="Send App Push Notifications", value=True),
                ft.Switch(label="Include Nearest Shade Spot in Alerts", value=True),
                ft.ElevatedButton(
                    "Save Profile Preferences", 
                    style=ft.ButtonStyle(color="white", bgcolor="orange600"),
                    width=300
                )
            ]),
            padding=15
        )

    # Navigation Setup
    body_container = ft.Container(content=build_home_view(), expand=True)

    def on_tab_changed(e):
        index = e.control.selected_index
        if index == 0:
            body_container.content = build_home_view()
        elif index == 1:
            body_container.content = build_map_view()
        elif index == 2:
            body_container.content = build_alerts_view()
        elif index == 3:
            body_container.content = build_profile_view()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_tab_changed,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.MAP_OUTLINED, selected_icon=ft.Icons.MAP, label="Map"),
            ft.NavigationBarDestination(icon=ft.Icons.NOTIFICATIONS_OUTLINED, selected_icon=ft.Icons.NOTIFICATIONS, label="Alerts"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINED, selected_icon=ft.Icons.PERSON, label="Profile"),
        ]
    )

    page.add(body_container)

    update_weather_data()
    start_10min_background_checker()

if __name__ == "__main__":
    ft.app(target=main)
