import socket
import threading
import tkinter as tk
from queue import Queue

class ServerGUI(tk.Tk):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.client_sockets = {}  # Dictionary to keep track of client sockets
        self.init_ui()

    def init_ui(self):
        self.title("Server Messages")
        self.geometry('800x600')

        self.text_area = tk.Text(self, height=20, width=100)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.message_entry = tk.Entry(self)
        self.message_entry.pack(padx=10, pady=10, fill=tk.X)

        self.send_button = tk.Button(self, text="Send Message to Client", command=self.send_message_to_client)
        self.send_button.pack(pady=10)

        self.after(100, self.process_queue)

    def process_queue(self):
        while not self.queue.empty():
            message = self.queue.get()
            self.text_area.insert(tk.END, message + "\n")
        self.after(100, self.process_queue)

    def send_message_to_client(self):
        message = self.message_entry.get()
        if message:
            # Assuming you want to broadcast to all connected clients
            for address, client_socket in self.client_sockets.items():
                try:
                    client_socket.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"Could not send message to {address}: {e}")

# --------------------------------------------------------------------------------------------
def client_handler(connection, address, queue, client_sockets):
    with connection:
        client_sockets[address] = connection
        queue.put(f"Client {address} connected")
        while True:
            try:
                data = connection.recv(1024).decode('utf-8')
                if not data:
                    break
                queue.put(f"Received '{data}' from {address}")
            except ConnectionResetError:
                queue.put(f"Client {address} has disconnected")
                break
        del client_sockets[address]
        queue.put(f"Client {address} connection closed")

# --------------------------------------------------------------------------------------------
def start_server(host, port, gui_queue, client_sockets):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        gui_queue.put(f"Server started on {host}:{port}. Waiting for connections...")
        
        while True:
            connection, address = server_socket.accept()
            threading.Thread(target=client_handler, args=(connection, address, gui_queue, client_sockets), daemon=True).start()

# --------------------------------------------------------------------------------------------
if __name__ == "__main__":
    gui_queue = Queue()
    client_sockets = {}
    server_gui = ServerGUI(gui_queue)
    
    host = 'localhost'
    port = 12345
    server_thread = threading.Thread(target=start_server, args=(host, port, gui_queue, client_sockets), daemon=True)
    server_thread.start()

    server_gui.mainloop()
