import socket
import threading
import time
from tkinter import (
    Tk, Label, Entry, Button, Toplevel,
    messagebox, END, simpledialog,
    Canvas, Frame, Scrollbar, Label as TkLabel
)

# ─── Konfigurasi Tampilan ──────────────────────────────────────────────
BG_COLOR      = "#1a1a2e"
TEXT_COLOR    = "#00f0ff"
ENTRY_COLOR   = "#222831"
BUTTON_COLOR  = "#0077ff"
FONT          = ("Orbitron", 12, "bold")

class ClientInterface:
    # ─── Login Window ──────────────────────────────────────────────────
    def __init__(self, master):
        self.master = master
        self.master.title("Login")
        self.master.geometry("400x300")
        self.master.config(bg=BG_COLOR)

        Label(master, text="Username:", bg=BG_COLOR, fg=TEXT_COLOR, font=FONT).pack(pady=5)
        self.entry_username = Entry(master, bg=ENTRY_COLOR, fg=TEXT_COLOR,
                                    insertbackground=TEXT_COLOR)
        self.entry_username.pack(pady=5)

        Label(master, text="Password:", bg=BG_COLOR, fg=TEXT_COLOR, font=FONT).pack(pady=5)
        self.entry_password = Entry(master, bg=ENTRY_COLOR, fg=TEXT_COLOR,
                                    show="*", insertbackground=TEXT_COLOR)
        self.entry_password.pack(pady=5)

        Button(master, text="Login", bg=BUTTON_COLOR, fg=TEXT_COLOR, font=FONT, command=self.login).pack(pady=10)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect(("192.168.56.1", 12345))   
        except Exception as e:
            messagebox.showerror("Error", f"Tidak dapat terhubung:\n{e}")
            self.client_socket = None

    # ─── Autentikasi ───────────────────────────────────────────────────
    def login(self):
        if self.client_socket is None:
            messagebox.showerror("Error", "Belum terkoneksi ke server.")
            return
        
        try:
        # Tunggu permintaan username dari server
            username_prompt = self.client_socket.recv(1024).decode()
            print(f"Server: {username_prompt}")
            self.client_socket.send(self.entry_username.get().encode())

        # Tunggu permintaan password dari server
            password_prompt = self.client_socket.recv(1024).decode()
            print(f"Server: {password_prompt}")
            self.client_socket.send(self.entry_password.get().encode())

        # Terima hasil dari server (berhasil/gagal)
            response = self.client_socket.recv(1024).decode()
            print(f"Server response: {response}")

            if "berhasil" in response.lower():
                messagebox.showinfo("Info", "Login berhasil!")
                self.open_chat_window()
            else:
                messagebox.showerror("Error", "Login gagal. Cek username dan password.")
        except Exception as e:
            messagebox.showerror("Error", f"Login error:\n{e}")


    # ─── Chat Window ───────────────────────────────────────────────────
    def open_chat_window(self):
        self.master.withdraw()
        self.chat_win = Toplevel()
        self.chat_win.title("Client Chat")
        self.chat_win.geometry("400x400")
        self.chat_win.config(bg=BG_COLOR)

        # Canvas + Frame + Scrollbar
        self.chat_canvas = Canvas(self.chat_win, bg=BG_COLOR, highlightthickness=0)
        self.chat_frame  = Frame(self.chat_canvas, bg=BG_COLOR)
        self.scrollbar   = Scrollbar(self.chat_win, command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.chat_canvas.pack(side="top", fill="both", expand=True)

        self.canvas_window = self.chat_canvas.create_window(
            (0, 0), window=self.chat_frame, anchor="nw", tags="chat_frame"
        )

        self.chat_frame.bind("<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>",
            lambda e: self.chat_canvas.itemconfig("chat_frame", width=e.width))

        # Frame bawah untuk input & tombol
        bottom_frame = Frame(self.chat_win, bg=BG_COLOR)
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.entry_message = Entry(bottom_frame, bg=ENTRY_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=FONT)
        self.entry_message.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)

        send_btn = Button(bottom_frame, text="Send", bg=BUTTON_COLOR, fg=TEXT_COLOR, font=FONT, command=self.send_message)
        send_btn.pack(side="right", pady=5)

        threading.Thread(target=self.receive_messages, daemon=True).start()

    # ─── Bubble Chat ───────────────────────────────────────────────────
    def add_bubble(self, msg, is_sender: bool):
        warna  = "#005f73" if is_sender else "#0a9396"
        anchor = "e" if is_sender else "w"

        container = Frame(self.chat_frame, bg=BG_COLOR)
        bubble = TkLabel(container, text=msg, bg=warna, fg="white",padx=10, pady=5, wraplength=300, justify="left")
        bubble.pack(anchor=anchor)
        container.pack(fill="x", anchor=anchor, padx=10, pady=2)

        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ─── Kirim Pesan ───────────────────────────────────────────────────
    def send_message(self):
        msg = self.entry_message.get()
        if not msg:
            return
        try:
            self.client_socket.send(msg.encode())
            self.add_bubble("Anda: " + msg, is_sender=True)
            self.entry_message.delete(0, END)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim: {e}")

    # ─── Minta Grafik Cuaca ────────────────────────────────────────────
    def request_weather_graph(self):
        kota = simpledialog.askstring("Kota", "Masukkan nama kota:")
        if kota:
            try:
                req = f"grafik cuaca {kota}"
                self.client_socket.send(req.encode())
                self.add_bubble(f"Anda meminta grafik cuaca untuk: {kota}", is_sender=True)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal mengirim: {e}")

    # ─── Terima Pesan ──────────────────────────────────────────────────
    def receive_messages(self):
        while True:
            try:
                msg = self.client_socket.recv(4096).decode()
                if not msg:
                    break
                self.add_bubble(msg, is_sender=False)

                with open("pesan_dari_server.txt", "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except:
                break

# ─── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = Tk()
    ClientInterface(root)
    root.mainloop()
