import socket
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import time

HOST = '127.0.0.1'
PORT = 5001

def send_file(filepath):
    filename = os.path.basename(filepath)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(filename.encode())

            time.sleep(0.2)  # Server'ın dosya adını önce alabilmesi için

            with open(filepath, "rb") as f:
                data = f.read(1024)
                while data:
                    s.sendall(data)
                    data = f.read(1024)

        messagebox.showinfo("Başarılı", f"'{filename}' dosyası gönderildi.")
    except Exception as e:
        messagebox.showerror("Hata", f"Bağlantı kurulamadı: {e}")

def select_and_send():
    filepath = filedialog.askopenfilename(title="Bir dosya seç",
                                          filetypes=[("Tüm dosyalar", "*.*")])
    if filepath:
        send_file(filepath)

root = tk.Tk()
root.title("İstemci - Dosya Gönder")

btn = tk.Button(root, text="Dosya Seç ve Gönder", command=select_and_send)
btn.pack(padx=20, pady=30)

root.mainloop()
