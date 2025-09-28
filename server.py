import socket
import threading
import tkinter as tk
from tkinter import Label, Text, Scrollbar, END, Button
from PIL import Image, ImageTk
import os
import subprocess
import platform
import sys

HOST = '127.0.0.1'
PORT = 5001

# Küresel değişkenler
server_socket = None
client_process = None
is_server_running = False

def open_file_with_default_app(filepath):
    system_name = platform.system()
    try:
        if system_name == "Windows":
            os.startfile(filepath)
        elif system_name == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        print("Dosya açılamadı:", e)

def handle_client(conn, addr, image_label, text_area):
    print(f"Bağlantı kuruldu: {addr}")
    try:
        filename = conn.recv(1024).decode()
    except Exception as e:
        print("Dosya adı alınamadı:", e)
        conn.close()
        return

    print(f"Gelen dosya: {filename}")
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".jpg", ".jpeg", ".png"]:
        folder = "gelen_resimler"
    elif ext == ".txt":
        folder = "gelen_textler"
    elif ext in [".mp4", ".avi", ".mp3", ".wav"]:
        folder = "gelen_videolar"
    else:
        folder = "others"

    if not os.path.exists(folder):
        os.makedirs(folder)

    filepath = os.path.join(folder, "gelen_" + filename)

    with open(filepath, "wb") as f:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            f.write(data)

    print("Dosya başarıyla kaydedildi:", filepath)

    if ext in [".jpg", ".jpeg", ".png"]:
        try:
            img = Image.open(filepath)
            img = img.resize((300, 300))
            img_tk = ImageTk.PhotoImage(img)
            image_label.config(image=img_tk)
            image_label.image = img_tk
            text_area.delete(1.0, END)
        except Exception as e:
            print("Resim gösterilemedi:", e)

    elif ext == ".txt":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            text_area.delete(1.0, END)
            text_area.insert(END, content)
            image_label.config(image='')
            image_label.image = None
        except Exception as e:
            print("Metin dosyası okunamadı:", e)

    elif ext in [".mp4", ".avi", ".mp3", ".wav"]:
        try:
            print("Video/Ses dosyası açılıyor...")
            open_file_with_default_app(filepath)
            image_label.config(image='')
            image_label.image = None
            text_area.delete(1.0, END)
        except Exception as e:
            print("Video/ses oynatılamadı:", e)
    else:
        print("Bilinmeyen dosya türü.")
        image_label.config(image='')
        image_label.image = None
        text_area.delete(1.0, END)

    conn.close()

def start_server(image_label, text_area, status_label, start_button, stop_button):
    global server_socket, client_process, is_server_running
    start_button.config(state=tk.DISABLED)
    status_label.config(text="Sunucu başlatılıyor...", fg="orange")

    def server_thread():
        global server_socket, client_process, is_server_running
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((HOST, PORT))
            server_socket.listen(5)
            is_server_running = True
            print(f"Sunucu dinleniyor: {HOST}:{PORT}")

            # Ana thread GUI öğelerini güncellemek için .after kullanıyoruz
            def gui_update_start():
                status_label.config(text=f"Sunucu başlatıldı: {HOST}:{PORT}", fg="green")
                stop_button.config(state=tk.NORMAL)

            root.after(0, gui_update_start)

            # Client başlat (shell=True kaldırıldı)
            try:
                if client_process and client_process.poll() is None:
                    print("Client zaten çalışıyor.")
                else:
                    client_process = subprocess.Popen([sys.executable, "client.py"])
                    print("Client başlatıldı.")
            except Exception as e:
                print("Client başlatılamadı:", e)

            while is_server_running:
                try:
                    server_socket.settimeout(1.0)
                    conn, addr = server_socket.accept()
                    threading.Thread(target=handle_client, args=(conn, addr, image_label, text_area), daemon=True).start()
                except socket.timeout:
                    continue
        except Exception as e:
            print("Sunucu başlatılamadı:", e)
            def gui_update_fail():
                status_label.config(text="Sunucu başlatılamadı!", fg="red")
                start_button.config(state=tk.NORMAL)
            root.after(0, gui_update_fail)

    threading.Thread(target=server_thread, daemon=True).start()

def stop_server(status_label, start_button, stop_button):
    global server_socket, client_process, is_server_running

    is_server_running = False

    # Socket'i kapat
    if server_socket:
        try:
            server_socket.close()
        except Exception as e:
            print("Socket kapatılamadı:", e)
        server_socket = None

    # Client process'i kapat
    if client_process:
        try:
            if client_process.poll() is None:  # Hâlâ çalışıyorsa
                client_process.terminate()
                client_process.wait(timeout=5)
            client_process = None
            print("Client kapatıldı.")
        except Exception as e:
            print("Client kapatılamadı:", e)

    status_label.config(text="Sunucu kapatıldı.", fg="red")
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

# === GUI ===
root = tk.Tk()
root.title("Sunucu - Gelen Dosya Gösterici")

label = Label(root, text="Resim Gösterimi:")
label.pack()

image_label = Label(root)
image_label.pack()

label2 = Label(root, text="Metin Dosyası İçeriği:")
label2.pack()

text_area = Text(root, height=10, width=50, wrap="word")
text_area.pack()

scrollbar = Scrollbar(root, command=text_area.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_area.config(yscrollcommand=scrollbar.set)

status_label = Label(root, text="Sunucu duruyor", fg="red")
status_label.pack(pady=5)

start_button = Button(root, text="Sunucuyu Başlat", command=lambda: start_server(image_label, text_area, status_label, start_button, stop_button))
start_button.pack(pady=5)

stop_button = Button(root, text="Sunucuyu Kapat", command=lambda: stop_server(status_label, start_button, stop_button))
stop_button.pack(pady=5)
stop_button.config(state=tk.DISABLED)

root.mainloop()
