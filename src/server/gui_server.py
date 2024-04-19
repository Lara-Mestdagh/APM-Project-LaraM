import socket
import threading
import tkinter as tk
from queue import Queue

class ServerGUI(tk.Tk):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.init_ui()

    def init_ui(self):
        self.title("Server Messages")
        # Set the initial size of the window (width x height)
        self.geometry('800x600')
        # You can adjust the 'width' and 'height' here for a larger text widget area
        self.text_area = tk.Text(self, height=20, width=100)  # Adjust the size as needed
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)        
        self.after(100, self.process_queue)

    def process_queue(self):
        while not self.queue.empty():
            message = self.queue.get()
            self.text_area.insert(tk.END, message + "\n")
        self.after(100, self.process_queue)

def client_handler(connection, address, queue):
    with connection:
        while True:
            data = connection.recv(1024).decode('utf-8')
            if not data or data.upper() == "EXIT":
                queue.put(f"Client {address} disconnected")
                break

            if data.upper() == "PING":
                response = "PONG"
            else:
                response = f"ECHO: {data}"
            
            queue.put(f"Received '{data}' from {address}, responding with '{response}'")
            connection.sendall(response.encode('utf-8'))

def start_server(host, port, gui_queue):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        gui_queue.put(f"Server started on {host}:{port}. Waiting for connections...")
        
        while True:
            connection, address = server_socket.accept()
            gui_queue.put(f"Connection established with {address}")
            threading.Thread(target=client_handler, args=(connection, address, gui_queue), daemon=True).start()

if __name__ == "__main__":
    gui_queue = Queue()
    server_gui = ServerGUI(gui_queue)
    
    host = 'localhost'
    port = 12345
    server_thread = threading.Thread(target=start_server, args=(host, port, gui_queue), daemon=True)
    server_thread.start()

    server_gui.mainloop()
