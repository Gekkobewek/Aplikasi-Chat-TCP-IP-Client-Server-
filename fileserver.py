import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import datetime

class ChatServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Server - LAN (Dictionary & Broadcast)")
        self.root.geometry("600x400")

        self.text_area = scrolledtext.ScrolledText(root, height=20, width=70)
        self.text_area.pack(padx=10, pady=10)

        self.start_button = tk.Button(root, text="Start Server", command=self.start_server)
        self.start_button.pack(pady=5)

        self.server_socket = None
        
        self.clients = {} 
        self.client_lock = threading.Lock()
        self.log_file = "server_log.txt"

    def log_message(self, message):
        """Mencatat pesan ke GUI dan file log."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.text_area.insert(tk.END, log_entry + "\n")
        self.text_area.see(tk.END)
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Gagal menulis log: {e}")

    def send_private_message(self, message, target_id):
        """Mengirim pesan privat menggunakan Dictionary lookup (O(1))."""
        with self.client_lock:
            # Mencari socket di looping list
            client_socket = self.clients.get(target_id)
            if client_socket:
                try:
                    # timestamp
                    server_ts = datetime.datetime.now().strftime("%H:%M:%S")
                    formatted_msg = f"[{server_ts}] {message}"
                    client_socket.send(formatted_msg.encode('ascii'))
                    return True
                except:
                    return False
        return False

    def broadcast_message(self, message, sender_socket):
        """
        [BAGIAN C: Implementasi Fitur Broadcast]
        Mengirim pesan ke semua client KECUALI pengirim.
        """
        with self.client_lock:
            server_ts = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{server_ts}] [BROADCAST] {message}"
            
            # Iterasi semua item di dictionary
            for client_id, client_socket in self.clients.items():
                if client_socket != sender_socket: # Jangan kirim balik ke pengirim
                    try:
                        client_socket.send(formatted_msg.encode('ascii'))
                    except:
                        continue

    def handle_client(self, client_socket, client_address, client_id):
        # Mendaftarkan client ke Dictionary
        with self.client_lock:
            self.clients[client_id] = client_socket
        
        self.log_message(f"Koneksi diterima dari {client_address} (ID: {client_id})")
        
        try:
            while True:
                data = client_socket.recv(1024).decode('ascii')
                if not data or data.lower() == 'exit':
                    break
                
                # TO:<target_id>:<message>
                if data.startswith("TO:"):
                    try:
                        _, target_id, msg_content = data.split(":", 2)
                        
                        # Logika Broadcast
                        if target_id.upper() == "ALL":
                            self.log_message(f"Broadcast dari {client_id}: {msg_content}")
                            self.broadcast_message(f"Dari {client_id}: {msg_content}", client_socket)
                        else:
                            # Logika Pesan Privat
                            self.log_message(f"Privat: {client_id} -> {target_id}: {msg_content}")
                            success = self.send_private_message(f"Dari {client_id}: {msg_content}", target_id)
                            if not success:
                                client_socket.send(f"Error: Client {target_id} tidak ditemukan".encode('ascii'))
                    except ValueError:
                        client_socket.send("Error: Format pesan salah (TO:<id>:<pesan>)".encode('ascii'))
        except Exception as e:
            self.log_message(f"Error pada {client_id}: {e}")
        finally:
            # Membersihkan Dictionary saat client putus
            with self.client_lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            client_socket.close()
            self.log_message(f"Client {client_id} terputus")

    def accept_connections(self):
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                # Client mengirim ID-nya terlebih dahulu
                client_id = client_socket.recv(1024).decode('ascii')
                threading.Thread(target=self.handle_client, args=(client_socket, client_address, client_id), daemon=True).start()
            except:
                break

    def start_server(self):
        host = '0.0.0.0' 
        port = 12345
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            
            # Mendapatkan IP asli laptop untuk memudahkan user
            actual_ip = socket.gethostbyname(socket.gethostname())
            self.log_message(f"Server berjalan. Listening pada {host}:{port}")
            self.log_message(f"IP Laptop Server ini: {actual_ip} (Gunakan IP ini di Client)")
            
            self.start_button.config(state='disabled')
            threading.Thread(target=self.accept_connections, daemon=True).start()
        except Exception as e:
            self.log_message(f"Error memulai server: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatServerGUI(root)
    root.mainloop()