import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import datetime

class ChatClientGUI:
    def __init__(self, root, client_id, server_ip):
        self.root = root
        self.client_id = client_id
        self.server_ip = server_ip
        self.server_port = 12345
        
        self.root.title(f"Chat Client - {client_id}")
        self.root.geometry("600x480")

        self.text_area = scrolledtext.ScrolledText(root, height=18, width=70)
        self.text_area.pack(padx=10, pady=10)

        # Frame Input
        input_frame = tk.Frame(root)
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="Kepada:").grid(row=0, column=0)
        self.target_entry = tk.Entry(input_frame, width=15)
        self.target_entry.grid(row=0, column=1, padx=5)
        self.target_entry.insert(0, "ALL") # Default broadcast sesuai permintaan

        tk.Label(input_frame, text="Pesan:").grid(row=0, column=2)
        self.message_entry = tk.Entry(input_frame, width=30)
        self.message_entry.grid(row=0, column=3, padx=5)
        self.message_entry.bind("<Return>", self.send_message)

        self.connect_button = tk.Button(root, text=f"Connect to {self.server_ip}", command=self.connect_to_server)
        self.connect_button.pack(pady=5)
        
        # Area info
        info_label = tk.Label(root, text="Ketik 'ALL' pada kolom 'Kepada' untuk Broadcast.", fg="blue")
        info_label.pack()

        self.client_socket = None
        self.running = True

    def log_message(self, message):
        self.text_area.insert(tk.END, f"{message}\n")
        self.text_area.see(tk.END)

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode('ascii')
                if not data: 
                    self.log_message("Koneksi ditutup oleh server.")
                    break
                self.log_message(data)
            except:
                break

    def send_message(self, event=None):
        target = self.target_entry.get().strip()
        msg = self.message_entry.get().strip()
        
        if target and msg and self.client_socket:
            # target ke pesan
            full_msg = f"TO:{target}:{msg}"
            try:
                self.client_socket.send(full_msg.encode('ascii'))
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_message(f"[{timestamp}] [ Me -> {target}]: {msg}")
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                self.log_message(f"Gagal mengirim: {e}")

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Menghubungkan ke IP Server yang diinput user
            self.client_socket.connect((self.server_ip, self.server_port))
            
            # Kirim ID Client sebagai langkah awal handshake
            self.client_socket.send(self.client_id.encode('ascii'))
            
            self.log_message(f"--- Terhubung ke {self.server_ip} sebagai {self.client_id} ---")
            self.connect_button.config(state='disabled')
            
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.log_message(f"Koneksi Gagal ke {self.server_ip}: {e}")
            messagebox.showerror("Error Koneksi", f"Tidak bisa menghubungi server di {self.server_ip}.\nPastikan Firewall Server Mati.")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # Sembunyikan window utama sementara
    
    # Input ID dan IP Server agar fleksibel antar laptop
    c_id = simpledialog.askstring("Setup", "Masukkan ID Client (misal: ClientA):")
    s_ip = simpledialog.askstring("Setup", "Masukkan IP Address Laptop Server:", initialvalue="192.168.1.X")
    
    if c_id and s_ip:
        root.deiconify() # Tampilkan kembali
        app = ChatClientGUI(root, c_id, s_ip)
        root.mainloop()
    else:
        root.destroy()