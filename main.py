# main.py  -- Modern Messenger (Kivy client)
# pip install kivy

import socket
import threading
import json
import uuid
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget

# Window settings (similar to 400x700 customtkinter window)
Window.size = (400, 700)
Window.clearcolor = (0.07, 0.07, 0.07, 1)  # Dark background


class LoginScreen(Screen):
    """Login UI: username + server + port"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", padding=20, spacing=15)

        # Title
        title = Label(
            text="💬 Modern Messenger",
            font_size=24,
            bold=True,
            size_hint=(1, None),
            height=40,
            color=(1, 1, 1, 1)
        )
        root.add_widget(Widget(size_hint_y=None, height=10))
        root.add_widget(title)

        subtitle = Label(
            text="Chat without phone numbers",
            font_size=14,
            size_hint=(1, None),
            height=20,
            color=(0.7, 0.7, 0.7, 1)
        )
        root.add_widget(subtitle)
        root.add_widget(Widget(size_hint_y=None, height=10))

        # Username input
        self.username_input = TextInput(
            hint_text="Enter your username",
            multiline=False,
            size_hint=(1, None),
            height=45,
            font_size=16
        )
        self.username_input.bind(on_text_validate=self.on_enter_pressed)
        root.add_widget(self.username_input)

        # Server + port row
        server_row = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, None), height=45)

        self.server_input = TextInput(
            hint_text="Server (localhost)",
            multiline=False,
            size_hint=(0.6, 1),
            text="localhost"
        )
        server_row.add_widget(self.server_input)

        self.port_input = TextInput(
            hint_text="Port (12345)",
            multiline=False,
            size_hint=(0.4, 1),
            text="12345"
        )
        server_row.add_widget(self.port_input)

        root.add_widget(server_row)

        # Join button
        self.join_btn = Button(
            text="Join Chat",
            size_hint=(1, None),
            height=50
        )
        self.join_btn.bind(on_press=self.join_chat)
        root.add_widget(self.join_btn)

        # Status label (better prompt/status)
        self.status_label = Label(
            text="Enter username and click Join Chat",
            font_size=13,
            size_hint=(1, None),
            height=25,
            color=(0.6, 0.8, 1, 1)
        )
        root.add_widget(self.status_label)

        # Instructions
        instructions = Label(
            text="Make sure server.py is running first!",
            font_size=12,
            size_hint=(1, None),
            height=20,
            color=(1, 0.9, 0.4, 1)
        )
        root.add_widget(instructions)

        root.add_widget(Widget())  # spacer

        self.add_widget(root)

    def on_enter_pressed(self, instance):
        self.join_chat()

    def show_error(self, message):
        self.status_label.text = message
        self.status_label.color = (1, 0.4, 0.4, 1)

    def show_info(self, message):
        self.status_label.text = message
        self.status_label.color = (0.6, 0.8, 1, 1)

    def join_chat(self, *args):
        username = self.username_input.text.strip()
        if not username:
            self.show_error("Please enter a username")
            return

        host = (self.server_input.text or "localhost").strip()
        port_text = (self.port_input.text or "12345").strip()
        try:
            port = int(port_text)
        except ValueError:
            self.show_error("Port must be a number")
            return

        app = App.get_running_app()
        self.join_btn.disabled = True
        self.show_info("Connecting...")

        def do_connect():
            try:
                app.connect_to_server(username, host, port)
                # Switch to chat screen on success
                def on_success(dt):
                    app.show_chat_screen()
                    self.join_btn.disabled = False
                Clock.schedule_once(on_success, 0)
            except Exception as e:
                msg = str(e)
                def on_fail(dt):
                    self.show_error(msg)
                    self.join_btn.disabled = False
                Clock.schedule_once(on_fail, 0)

        threading.Thread(target=do_connect, daemon=True).start()


class ChatScreen(Screen):
    """Main chat UI: header + messages + input"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._joined_once = False

        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Header bar
        header = BoxLayout(orientation="horizontal",
                           size_hint=(1, None),
                           height=50,
                           padding=(5, 5, 5, 5),
                           spacing=10)

        self.chat_title_label = Label(
            text="💬 General Chat",
            font_size=18,
            bold=True,
            size_hint=(0.6, 1),
            color=(1, 1, 1, 1)
        )
        header.add_widget(self.chat_title_label)

        self.user_info_label = Label(
            text="👤",
            font_size=13,
            size_hint=(0.4, 1),
            color=(0.6, 0.8, 1, 1),
            halign="right",
            valign="middle"
        )
        self.user_info_label.bind(size=self._update_user_label)
        header.add_widget(self.user_info_label)

        root.add_widget(header)

        # Scrollable messages area
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.messages_layout = GridLayout(cols=1, spacing=5, size_hint_y=None, padding=(0, 0, 0, 10))
        self.messages_layout.bind(minimum_height=self.messages_layout.setter("height"))
        self.scroll_view.add_widget(self.messages_layout)
        root.add_widget(self.scroll_view)

        # Input area
        input_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=60, spacing=10)

        self.message_input = TextInput(
            hint_text="Type your message...",
            multiline=False,
            size_hint=(0.8, 1),
            font_size=14
        )
        self.message_input.bind(on_text_validate=self.send_message)
        input_row.add_widget(self.message_input)

        self.send_btn = Button(
            text="Send",
            size_hint=(0.2, 1)
        )
        self.send_btn.bind(on_press=self.send_message)
        input_row.add_widget(self.send_btn)

        root.add_widget(input_row)

        self.add_widget(root)

    def _update_user_label(self, instance, size):
        # Ensure right alignment
        self.user_info_label.text_size = (size[0], size[1])

    def on_joined(self):
        """Called by the App once after successful join."""
        app = App.get_running_app()
        self.user_info_label.text = f"👤 {app.username}"

        if not self._joined_once:
            self.add_system_message("Welcome to the chat! Start messaging...")
            self.add_system_message(f"You joined as {app.username}")
            self._joined_once = True

    def scroll_to_bottom(self, *args):
        # In Kivy, scroll_y=0 is bottom
        self.scroll_view.scroll_y = 0

    def add_system_message(self, text):
        lbl = Label(
            text=text,
            font_size=12,
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None,
            halign="center",
            valign="middle"
        )
        lbl.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w, None)),
            texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + 10)
        )
        self.messages_layout.add_widget(lbl)
        Clock.schedule_once(self.scroll_to_bottom, 0.05)

    def add_user_message(self, username, message, is_me=False):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

        # Spacer & bubble alignment
        if is_me:
            row.add_widget(Widget(size_hint_x=0.2))
        bubble = BoxLayout(
            orientation="vertical",
            size_hint_x=0.8,
            padding=(10, 6, 10, 6),
        )

        if not is_me:
            user_lbl = Label(
                text=f"[b]{username}[/b]",
                markup=True,
                font_size=12,
                size_hint_y=None,
                color=(0.6, 0.8, 1, 1),
                halign="left",
                valign="middle"
            )
            user_lbl.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", ts[1])
            )
            bubble.add_widget(user_lbl)

        msg_lbl = Label(
            text=message,
            font_size=14,
            size_hint_y=None,
            halign="left",
            valign="top",
            color=(1, 1, 1, 1 if is_me else 0.9)
        )
        msg_lbl.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w * 0.95, None)),
            texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + 5)
        )
        bubble.add_widget(msg_lbl)

        # background "bubble" color via canvas
        with bubble.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            if is_me:
                Color(0.35, 0.4, 0.95, 1)  # bluish for me
            else:
                Color(0.25, 0.27, 0.3, 1)
            bubble._bg = RoundedRectangle(radius=[15, 15, 15, 15])
        bubble.bind(
            pos=lambda inst, pos: setattr(bubble._bg, "pos", pos),
            size=lambda inst, size: setattr(bubble._bg, "size", size),
        )

        row.add_widget(bubble)
        if not is_me:
            row.add_widget(Widget(size_hint_x=0.2))

        # Adjust row height when content grows
        def update_row_height(*_):
            total = 0
            for child in bubble.children:
                total += child.height
            row.height = total + 20

        bubble.bind(children=lambda *a: update_row_height())
        msg_lbl.bind(height=lambda *a: update_row_height())

        self.messages_layout.add_widget(row)
        Clock.schedule_once(self.scroll_to_bottom, 0.05)

    def display_message(self, message_data):
        if message_data.get("type") == "system":
            self.add_system_message(message_data.get("message", ""))
        else:
            app = App.get_running_app()
            is_me = (message_data.get("user_id") == app.user_id)
            self.add_user_message(
                message_data.get("username", "Unknown"),
                message_data.get("message", ""),
                is_me=is_me
            )

    def send_message(self, *args):
        app = App.get_running_app()
        text = self.message_input.text.strip()
        if not text or not app.connected or app.socket is None:
            return

        message_data = {
            "type": "message",
            "user_id": app.user_id,
            "username": app.username,
            "message": text,
            "timestamp": datetime.now().isoformat()
        }

        try:
            app.socket.send((json.dumps(message_data) + "\n").encode("utf-8"))
            self.message_input.text = ""
        except Exception:
            self.add_system_message("❌ Failed to send message")


class ModernMessengerApp(App):
    """Main Kivy App with networking logic shared between screens."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.host = "localhost"
        self.port = 12345
        self.socket = None
        self.username = ""
        self.user_id = str(uuid.uuid4())
        self.connected = False

    def build(self):
        self.title = "Modern Messenger (Kivy)"
        self.sm = ScreenManager(transition=SlideTransition())
        self.login_screen = LoginScreen(name="login")
        self.chat_screen = ChatScreen(name="chat")
        self.sm.add_widget(self.login_screen)
        self.sm.add_widget(self.chat_screen)
        return self.sm

    def connect_to_server(self, username, host, port):
        self.username = username
        self.host = host
        self.port = port

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)

        try:
            s.connect((host, port))
        except socket.timeout:
            s.close()
            raise Exception("Connection timeout - Server not responding")
        except ConnectionRefusedError:
            s.close()
            raise Exception("❌ Connection refused - Start server.py first!")
        except Exception as e:
            s.close()
            raise Exception(f"Connection failed: {e}")

        s.settimeout(None)
        self.socket = s
        self.connected = True

        # Send join info
        join_data = {
            "type": "join",
            "user_id": self.user_id,
            "username": self.username
        }
        self.socket.send((json.dumps(join_data) + "\n").encode("utf-8"))

        # Start receive thread
        t = threading.Thread(target=self.receive_messages, daemon=True)
        t.start()

    def receive_messages(self):
        buffer = ""
        while self.connected and self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                data = data.decode("utf-8")
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        Clock.schedule_once(lambda dt, m=msg: self.chat_screen.display_message(m), 0)
            except Exception:
                break

        # Connection lost
        if self.connected:
            self.connected = False
            Clock.schedule_once(
                lambda dt: self.chat_screen.add_system_message("❌ Lost connection to server"),
                0
            )

    def show_chat_screen(self):
        self.chat_screen.on_joined()
        self.sm.current = "chat"


if __name__ == "__main__":
    print("🚀 Starting Modern Messenger (Kivy Client)...")
    print("👉 Make sure server.py is running before you join the chat.")
    ModernMessengerApp().run()
