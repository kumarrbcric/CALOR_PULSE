import flet as ft
import requests

# Live Python Backend URL on Render
SERVER_URL = "https://calor-pulse.onrender.com"

def main(page: ft.Page):
    page.title = "CalorPulse - Heat Monitor"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # UI Form Fields
    title_text = ft.Text("CalorPulse", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400)
    subtitle_text = ft.Text("Heat Risk Alert Registration", size=14, color=ft.Colors.GREY_400)
    
    age_input = ft.TextField(
        label="Age", 
        keyboard_type=ft.KeyboardType.NUMBER, 
        width=300,
        hint_text="e.g. 20"
    )
    
    cond_input = ft.TextField(
        label="Health Conditions (comma separated)", 
        width=300,
        hint_text="e.g. Heart disease, Asthma"
    )
    
    shade_switch = ft.Switch(
        label="Find Nearest Shade Spot", 
        value=True
    )
    
    status_text = ft.Text(value="", size=14)

    # Registration Button Event Logic
    def register_user(e):
        status_text.value = "Registering with server..."
        status_text.color = ft.Colors.BLUE_400
        page.update()

        # Build payload matching app logic
        payload = {
            "token": "ExponentPushToken[SamplePythonDeviceToken]",  # Device Push Token
            "lat": 10.7905,  # Replace with dynamic GPS location if needed
            "lon": 78.7047,
            "age": int(age_input.value) if age_input.value and age_input.value.isdigit() else 20,
            "cond": [c.strip() for c in cond_input.value.split(",") if c.strip()],
            "shade": shade_switch.value
        }

        try:
            response = requests.post(f"{SERVER_URL}/register", json=payload, timeout=10)
            if response.status_code == 200:
                status_text.value = "Registered! You will receive heat alerts."
                status_text.color = ft.Colors.GREEN_400
            else:
                status_text.value = f"Server Error: {response.status_code}"
                status_text.color = ft.Colors.RED_400
        except Exception as err:
            status_text.value = f"Connection Failed: {err}"
            status_text.color = ft.Colors.RED_400
        
        page.update()

    submit_button = ft.ElevatedButton(
        "Enable Heat Risk Alerts", 
        on_click=register_user,
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bg_color=ft.Colors.ORANGE_600),
        width=300
    )

    # Layout structure
    page.add(
        title_text,
        subtitle_text,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        age_input,
        cond_input,
        shade_switch,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        submit_button,
        status_text
    )

if __name__ == "__main__":
    ft.app(target=main)
