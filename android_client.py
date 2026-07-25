import os
import threading
import time

import requests
from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

try:
    from plyer import notification
except ImportError:
    notification = None

SERVER_URL = os.getenv("MISSION_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


class MissionLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=12, padding=20, **kwargs)
        self.last_event_id = 0
        self.title_input = TextInput(hint_text="Describe la mision", multiline=False, size_hint_y=None, height=50)
        self.add_widget(Label(text="Misiones de Aitana", font_size=24, size_hint_y=None, height=60))
        self.add_widget(self.title_input)
        send_button = Button(text="Crear mision para Benja", size_hint_y=None, height=52)
        send_button.bind(on_press=self.create_mission)
        self.add_widget(send_button)
        self.status = Label(text=f"Servidor: {SERVER_URL}")
        self.add_widget(self.status)
        threading.Thread(target=self.poll_events, daemon=True).start()

    def create_mission(self, _button):
        title = self.title_input.text.strip()
        if not title:
            self.status.text = "Escribe una mision primero."
            return
        try:
            response = requests.post(
                f"{SERVER_URL}/missions",
                json={"creator": "aitana", "title": title},
                timeout=5,
            )
            response.raise_for_status()
            self.title_input.text = ""
            self.status.text = "Mision enviada a Windows"
        except requests.RequestException as error:
            self.status.text = f"Error: {error}"

    def poll_events(self):
        while True:
            try:
                response = requests.get(
                    f"{SERVER_URL}/events",
                    params={"target": "android", "after": self.last_event_id},
                    timeout=5,
                )
                response.raise_for_status()
                for event in response.json():
                    self.last_event_id = max(self.last_event_id, event["id"])
                    self.show_notification(event)
            except requests.RequestException:
                pass
            time.sleep(3)

    @mainthread
    def show_notification(self, event):
        self.status.text = f"Nueva mision de Benja: {event['title']}"
        if notification:
            notification.notify(title="Nueva mision de Benja", message=event["title"], app_name="Misiones")


class MissionsApp(App):
    def build(self):
        return MissionLayout()


if __name__ == "__main__":
    MissionsApp().run()
