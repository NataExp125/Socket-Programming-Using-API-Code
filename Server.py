import socket
import threading
import requests
from tkinter import Tk, Text, Scrollbar, Entry, Button, END
import datetime

# Konfigurasi warna dan font
BG_COLOR      = "#1a1a2e"
TEXT_COLOR    = "#00f0ff"
SERVER_COLOR  = "#ffcc00"
CLIENT_COLOR  = "#00ff88"
WARNING_COLOR = "#ff3355"
ENTRY_COLOR   = "#222831"
BUTTON_COLOR  = "#0077ff"
FONT          = ("Orbitron", 12, "bold")

# URL dan API key untuk cuaca
API_URL = "https://api.weatherapi.com/v1/current.json"
API_URL = "https://api.weatherapi.com/v1/forecast.json"
API_KEY = "523ea81486a145f087e45229230706"

# Fungsi untuk mendapatkan cuaca saat ini
def get_current_weather(location: str) -> str:
    try:
        params = { "key": API_KEY, "q": location, "aqi": "no" }
        res = requests.get(API_URL, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        loc = data["location"]["name"]
        cur = data["current"]
        return (
            f"Cuaca di {loc}:\n"
            f"- Suhu: {cur['temp_c']}°C\n"
            f"- Kelembaban: {cur['humidity']}%\n"
            f"- Kondisi: {cur['condition']['text']}\n"
            f"- Tekanan udara: {cur['pressure_mb']} hPa\n"
            f"- Kecepatan angin: {cur['wind_kph']} km/jam\n"
            f"- Arah angin: {cur['wind_dir']}"
        )
    except Exception as e:
        return f"Gagal ambil data cuaca: {e}"

# Fungsi untuk mendapatkan cuaca selama 3 hari
def get_weather_forecast(location: str) -> str:
    try:
        params = { "key": API_KEY, "q": location, "days": 3, "aqi": "no", "alerts": "no" }
        res = requests.get(API_URL, params=params, timeout=5)
        res.raise_for_status()  
        data = res.json()
        loc = data["location"]["name"]
        forecast = data["forecast"]["forecastday"]
        forecast_str = f"Cuaca 3 Hari di {loc}:\n"
        today = datetime.datetime.now()
        for i, day in enumerate(forecast):
            date = today + datetime.timedelta(days=i)  
            formatted_date = date.strftime("%Y-%m-%d") 
            temp_max = day["day"]["maxtemp_c"]
            temp_min = day["day"]["mintemp_c"]
            condition = day["day"]["condition"]["text"]
            forecast_str += f"\n{formatted_date}\n, Kondition: {condition}\n, Max: {temp_max}°C\n, Min: {temp_min}°C\n"
        
        return forecast_str
    except Exception as e:
        return f"Gagal ambil data cuaca: {e}"

#class ServerInterface untuk antarmuka server
class ServerInterface:
    def __init__(self, master):
        self.master      = master
        self.master.title("Server Chat & Weather")
        self.master.config(bg=BG_COLOR)

        # Server & client storage
        self.server       = None
        self.clients      = {} 
        self.credentials  = {
            "Nata":      "admin1234",
            "Mr.Agung":  "admin1234",
            "Mr.Rokhmat":"admin1234"
        }

        # Text widget untuk log
        self.text_area = Text(
            master, state="disabled", wrap="word",
            bg=BG_COLOR, fg=TEXT_COLOR, font=FONT,
            padx=10, pady=10
        )
        self.text_area.pack(padx=10, pady=10, fill="both", expand=True)

        # Scrollbar
        self.scrollbar = Scrollbar(master, command=self.text_area.yview)
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Entry + Button untuk broadcast manual
        self.entry_message = Entry(
            master, width=50,
            bg=ENTRY_COLOR, fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR, font=FONT
        )
        self.entry_message.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.button_send = Button(
            master, text="Send to All",
            bg=BUTTON_COLOR, fg=TEXT_COLOR,
            font=FONT, command=self.broadcast_message
        )
        self.button_send.pack(side="right", padx=10, pady=10)

        # Start server
        self.start_server()

    # fungsi untuk memulai server
    def start_server(self):
        host = "0.0.0.0"
        port = 12345
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.append_text(f"✔ Server berjalan di {host}:{port}", SERVER_COLOR)
        threading.Thread(target=self.accept_clients, daemon=True).start()

    #fungsi untuk menerima koneksi dari client
    def accept_clients(self):
        while True:
            client_sock, addr = self.server.accept()
            self.append_text(f"🔗 Koneksi dari {addr}", SERVER_COLOR)
            threading.Thread(
                target=self.handle_client,
                args=(client_sock,),
                daemon=True
            ).start()
    #fungsi untuk menangani koneksi dari client
    def handle_client(self, client_sock):
        username = None
        try:
            # Autentikasi
            client_sock.send(b"Username: ")
            username = client_sock.recv(1024).decode().strip()
            client_sock.send(b"Password: ")
            password = client_sock.recv(1024).decode().strip()

            if username in self.credentials and self.credentials[username] == password:
                client_sock.send(b"Login berhasil\n")
                self.append_text(f"👤 {username} berhasil login", CLIENT_COLOR)
                self.clients.setdefault(username, []).append(client_sock)

                client_sock.send(f"Selamat Datang, {username}😊🙏\n".encode())
                instructions = (
                    "\nCara menggunakan aplikasi:\n"
                    "1. Untuk mengecek cuaca, ketik: 'cuaca <lokasi>'\n"
                    "   Contoh: cuaca Jakarta\n"
                    "2. Untuk cuaca selama 3 hari,ketik:'forecast<lokasi>'\n"
                    "   Contoh: forecast Jakarta\n"
                    "3. Untuk keluar dari aplikasi, ketik 'exit'\n"
                    "Semoga aplikasi ini bermanfaat! 🌟"
                )
                client_sock.send(instructions.encode())
            else:
                client_sock.send(b"Autentikasi gagal\n")
                self.append_text(f"⚠️ Login gagal: {username}", WARNING_COLOR)
                client_sock.close()
                return

            # Loop menerima pesan
            while True:
                data = client_sock.recv(1024)
                if not data:
                    break
                msg = data.decode().strip()

                if msg.lower() == "exit":
                    self.append_text(f"🚪 {username} keluar", WARNING_COLOR)
                    break

                # input cuaca, format: "cuaca <lokasi>"
                if msg.lower().startswith(("cuaca ", "weather ")):
                    _, loc = msg.split(maxsplit=1)
                    resp = get_current_weather(loc)
                    client_sock.sendall(resp.encode())
                    self.append_text(f"→ Request cuaca: {loc}", SERVER_COLOR)
                    continue

                # input cuaca 3 hari, format: "forecast <lokasi>"
                if msg.lower().startswith(("forecast ", "forecast3 ")):
                    _, loc = msg.split(maxsplit=1)
                    resp = get_weather_forecast(loc)
                    client_sock.sendall(resp.encode())
                    self.append_text(f"→ Request cuaca 3 hari: {loc}", SERVER_COLOR)
                    continue

                # Broadcast chat biasa
                self.append_text(f"{username}: {msg}", CLIENT_COLOR)
                self.broadcast_message(f"{username}: {msg}", exclude=client_sock)

        except Exception as e:
            self.append_text(f"❌ Error dengan {username}: {e}", WARNING_COLOR)

        finally:
            # untuk menutup koneksi
            client_sock.close()
            if username in self.clients:
                self.clients[username] = [
                    s for s in self.clients[username] if s != client_sock
                ]
                if not self.clients[username]:
                    del self.clients[username]

    # Fungsi untuk mengirim pesan ke semua client
    def broadcast_message(self, message=None, exclude=None):
        # Jika dipicu tombol server
        if message is None:
            message = f"Server: {self.entry_message.get()}"
            self.entry_message.delete(0, END)
        color = SERVER_COLOR if message.startswith("Server:") else CLIENT_COLOR
        self.append_text(message, color)

        for sock_list in self.clients.values():
            for sock in sock_list:
                if sock != exclude:
                    try:
                        sock.sendall(message.encode())
                    except Exception as e:
                        self.append_text(f"⚠️ Broadcast error: {e}", WARNING_COLOR)

    # Fungsi untuk menambahkan teks ke area teks
    def append_text(self, msg, color=TEXT_COLOR):
        self.text_area.config(state="normal")
        self.text_area.insert(END, msg + "\n")
        start = f"end-{len(msg)+1}c"
        self.text_area.tag_add("msg", start, "end-1c")
        self.text_area.tag_config("msg", foreground=color, font=FONT, background=BG_COLOR)
        self.text_area.config(state="disabled")
        self.text_area.yview(END)

#memanggil fungsi utama untuk menjalankan server
if __name__ == "__main__":
    root = Tk()
    app = ServerInterface(root)
    root.mainloop()
