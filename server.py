import socket
import threading
import tkinter as tk
from tkinter import Label, Text, Scrollbar, END
from PIL import Image, ImageTk
import os
import subprocess
import platform

HOST = '127.0.0.1'
PORT = 5001

def open_file_with_default_app(filepath):
    system_name = platform.system()
    try:
        if system_name == "Windows":
            os.startfile(filepath)  # Windows'ta en temiz yöntem
        elif system_name == "Darwin":  # macOS
            subprocess.Popen(["open", filepath])
        else:  # Linux ve diğerleri
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

    # Klasör yoksa oluştur
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
    # GUI'de gösterme mantığı
    if ext in [".jpg", ".jpeg", ".png"]:
        try:
            img = Image.open(filepath)
            img = img.resize((300, 300))
            img_tk = ImageTk.PhotoImage(img)
            image_label.config(image=img_tk)
            image_label.image = img_tk
            text_area.delete(1.0, END)  # Metin alanını temizle
        except Exception as e:
            print("Resim gösterilemedi:", e)

    elif ext == ".txt":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            text_area.delete(1.0, END)
            text_area.insert(END, content)
            image_label.config(image='')  # Resim alanını temizle
            image_label.image = None
        except Exception as e:
            print("Metin dosyası okunamadı:", e)

    elif ext in [".mp4", ".avi", ".mp3", ".wav"]:
        try:
            print("Video/Ses dosyası açılıyor...")
            open_file_with_default_app(filepath)
            image_label.config(image='')  # Temizle
            image_label.image = None
            text_area.delete(1.0, END)
        except Exception as e:
            print("Video/ses oynatılamadı:", e)

    else:
        print("Bilinmeyen dosya türü.")
        image_label.config(image='')  # Temizle
        image_label.image = None
        text_area.delete(1.0, END)

    conn.close()

def start_server(image_label, text_area):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Server dinleniyor: {HOST}:{PORT}")

    def accept_connection():
        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, image_label, text_area))
            client_thread.start()

    threading.Thread(target=accept_connection, daemon=True).start()

# GUI
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

start_server(image_label, text_area)
root.mainloop()
