import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, Text, END
from PIL import Image, ImageTk
import os
import time
import subprocess
import platform
import sys

# Sunucu ile iletişim için
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001

# Kapatma komutu dinlemesi için
CONTROL_PORT = 6000  # Bu portu server üzerinden kapatma komutu için kullanacağız

sent_files = []

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
        messagebox.showerror("Hata", f"Dosya açılamadı: {e}")

def send_file(filepath):
    filename = os.path.basename(filepath)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            s.sendall(filename.encode('utf-8'))
            time.sleep(0.2)

            with open(filepath, "rb") as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    s.sendall(data)

        messagebox.showinfo("Başarılı", f"'{filename}' dosyası gönderildi.")
        if filename not in sent_files:
            sent_files.append(filename)
            file_listbox.insert(END, filename)

    except ConnectionRefusedError:
        messagebox.showerror("Hata", "Sunucu aktif değil.")
    except Exception as e:
        messagebox.showerror("Hata", f"Hata oluştu:\n{e}")

def select_and_send():
    filepath = filedialog.askopenfilename(
        title="Bir dosya seç",
        filetypes=[
            ("Tüm dosyalar", "*.*"),
            ("Resimler", "*.jpg *.jpeg *.png"),
            ("Metin Dosyaları", "*.txt"),
            ("Video/Ses", "*.mp4 *.avi *.mp3 *.wav"),
        ]
    )
    if filepath:
        send_file(filepath)

def display_selected_file():
    selected = file_listbox.curselection()
    if not selected:
        messagebox.showwarning("Uyarı", "Lütfen bir dosya seçin.")
        return

    filename = file_listbox.get(selected[0])
    folders = ["gelen_resimler", "gelen_textler", "gelen_videolar", "others"]
    for folder in folders:
        path = os.path.join(folder, "gelen_" + filename)
        if os.path.exists(path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                img = Image.open(path)
                img = img.resize((300, 300))
                img_tk = ImageTk.PhotoImage(img)
                image_label.config(image=img_tk)
                image_label.image = img_tk
                text_area.delete(1.0, END)
            elif ext == ".txt":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                text_area.delete(1.0, END)
                text_area.insert(END, content)
                image_label.config(image='')
                image_label.image = None
            else:
                open_file_with_default_app(path)
            return
    messagebox.showerror("Bulunamadı", "Dosya yerel diskte bulunamadı.")

def listen_for_shutdown():
    def shutdown_thread():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', CONTROL_PORT))
                s.listen(1)
                conn, _ = s.accept()
                msg = conn.recv(1024).decode()
                if msg == "kapat":
                    print("Kapat komutu alındı.")
                    root.quit()  # GUI kapatılır
        except Exception as e:
            print("Kapatma dinleyicisi hata verdi:", e)

    threading.Thread(target=shutdown_thread, daemon=True).start()

# === GUI ===
root = tk.Tk()
root.title("İstemci - Dosya Gönder ve Göster")

btn = tk.Button(root, text="Dosya Seç ve Gönder", command=select_and_send)
btn.pack(padx=20, pady=10)

file_listbox = Listbox(root, width=40, height=6)
file_listbox.pack()

pull_btn = tk.Button(root, text="Seçili Dosyayı Göster", command=display_selected_file)
pull_btn.pack(pady=10)

image_label = tk.Label(root)
image_label.pack()

text_area = Text(root, height=10, width=50)
text_area.pack()

scrollbar = Scrollbar(root, command=text_area.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_area.config(yscrollcommand=scrollbar.set)

listen_for_shutdown()
root.mainloop()
