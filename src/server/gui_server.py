import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from queue import Queue
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ServerGUI(tk.Tk):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.clients = {}
        self.client_vars = {}

        self.init_ui()
        self.after(100, self.process_queue)

    def init_ui(self):
        self.title("Server Messages")
        self.geometry("800x600")

        self.text_area = scrolledtext.ScrolledText(self, height=10, width=50)
        self.text_area.pack(padx=10, pady=10)

        self.message_entry = tk.Entry(self)
        self.message_entry.pack(fill=tk.X, padx=10, pady=10)
        
        self.send_button = tk.Button(self, text="Send Message to Selected Clients", command=self.send_message_to_clients)
        self.send_button.pack(pady=10)

        self.client_list_frame = tk.LabelFrame(self, text="Connected Clients")
        self.client_list_frame.pack(fill=tk.BOTH, expand=True)

    def process_queue(self):
        while not self.queue.empty():
            addr, connected = self.queue.get()
            if connected:
                var = tk.BooleanVar(value=False)
                rb = tk.Checkbutton(self.client_list_frame, text=str(addr), variable=var)
                rb.pack(anchor='w')
                self.client_vars[addr] = var
                self.clients[addr] = connected
            else:
                if addr in self.client_vars:
                    self.client_vars[addr].get_widget().destroy()
                    del self.client_vars[addr]
                    del self.clients[addr]
        self.after(100, self.process_queue)

    def send_message_to_clients(self):
        message = self.message_entry.get()
        message += "\n"
        for addr, var in self.client_vars.items():
            if var.get():
                client = self.clients[addr]
                try:
                    client.send(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Failed to send message to {addr}: {e}")

def client_handler(client_socket, addr, gui_queue):
    with client_socket:
        gui_queue.put((addr, client_socket))  # Notify GUI of new connection
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data or data == "EXIT":
                    break
                if data == "PING":
                    client_socket.send("PONG".encode('utf-8'))
                logging.info(f"Received from {addr}: {data}")
        finally:
            client_socket.close()
            gui_queue.put((addr, None))  # Signal client disconnection
            logging.info(f"Client {addr} has disconnected")

def start_server(host, port, gui_queue):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        logging.info(f"Server started on {host}:{port}")

        while True:
            client_sock, addr = server_socket.accept()
            threading.Thread(target=client_handler, args=(client_sock, addr, gui_queue), daemon=True).start()

if __name__ == "__main__":
    gui_queue = Queue()
    server_gui = ServerGUI(gui_queue)
    
    host = 'localhost'
    port = 12345
    server_thread = threading.Thread(target=start_server, args=(host, port, gui_queue), daemon=True)
    server_thread.start()

    server_gui.mainloop()
