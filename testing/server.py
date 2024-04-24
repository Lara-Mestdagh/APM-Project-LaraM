import os
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, Listbox, simpledialog
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ServerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Server Dashboard")
        self.geometry("800x400")
        self.active_clients = {}  # Dictionary to track clients
        self.initUI()
        self.server_running = True

        self.log_queue = Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.queue_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(self.queue_handler)
        logger.setLevel(logging.INFO)

        self.queue_listener = QueueListener(self.log_queue, self.queue_handler)
        self.queue_listener.start()

    def initUI(self):
        self.log_widget = scrolledtext.ScrolledText(self, state='disabled', height=10, width=70)
        self.log_widget.pack(padx=10, pady=5)

        self.message_entry = tk.Entry(self)
        self.message_entry.pack(fill=tk.X, padx=10, pady=10)
        
        self.send_button = tk.Button(self, text="Send Message to Selected Clients", command=self.send_message_to_clients)
        self.send_button.pack(pady=10)

        self.client_list_frame = tk.LabelFrame(self, text="Connected Clients")
        self.client_list_frame.pack(fill=tk.BOTH, expand=True)

        self.client_list_box = Listbox(self, height=10, width=70)
        self.client_list_box.pack(padx=10, pady=5)

    def UpdateClientList(self):
        self.client_list_box.delete(0, tk.END)
        for client in self.active_clients.keys():
            self.client_list_box.insert(tk.END, f"{client} - {self.active_clients[client]}")
    
    def addClient(self, client_id, address):
        self.active_clients[client_id] = address
        self.UpdateClientList()
        logging.info(f"Added client {client_id} from {address}")

    def remove_client(self, client_id):
        if client_id in self.active_clients:
            address = self.active_clients[client_id]
            del self.active_clients[client_id]
            self.UpdateClientList()
            logging.info(f"Removed client {client_id} from {address}")

    def send_message_to_clients(self):
        message = self.message_entry.get()
        message += "\n"
        for addr, var in self.active_clients.items():
            if var.get():
                client = self.clients[addr]
                try:
                    # log message sent to client
                    logging.info(f"Sending message to {addr}: {message}")
                    client.send(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Failed to send message to {addr}: {e}")

    def exitApp(self):
        self.server_running = False  # Flag to stop the server loop
        self.queue_listener.stop()   # Stop the logging queue listener
        self.destroy()  # Close the GUI window

    def handleLogEvent(self, record):
        msg = self.queue_handler.format(record)
        self.log_widget.configure(state='normal')
        self.log_widget.insert(tk.END, msg + '\n')
        self.log_widget.configure(state='disabled')
        self.log_widget.yview(tk.END)

    def onClosing(self):
        self.queue_listener.stop()
        self.destroy()

def handleClient(connection, address, app):
    client_id = threading.get_ident()
    try:
        app.addClient(client_id, str(address))
        logging.info(f"Client connected from {address}")

        with connection.makefile('rw', buffering=1) as conn_file:
            while True:
                message = conn_file.readline().strip()
                if message == "CLOSE":
                    logging.info(f"Client from {address} requested to close the connection")
                    break
                # Additional message handling logic here
    except Exception as e:
        logging.error(f"Error handling connection with {address}: {e}")
    finally:
        app.remove_client(client_id)
        logging.info(f"Client disconnected from {address}")
        connection.close()

def registerUser(username, password):
    # This function will append the username and password to a file
    with open("user_credentials.txt", "a") as file:
        file.write(f"{username} {password}\n")

def checkCredentials(username, password):
    # This function checks if the provided username and password match any stored credentials
    if os.path.exists("user_credentials.txt"):
        with open("user_credentials.txt", "r") as file:
            for line in file:
                stored_username, stored_password = line.strip().split()
                if stored_username == username and stored_password == password:
                    return True
    return False

def startServer(app, host='0.0.0.0', port=12345):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    logging.info(f"Server listening on {host}:{port}")

    try:
        while app.server_running:
            client_conn, client_addr = server_socket.accept()
            client_thread = threading.Thread(target=handleClient, args=(client_conn, client_addr, app))
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Server is shutting down")
    finally:
        server_socket.close()

if __name__ == "__main__":
    app = ServerGUI()
    # Ensure the server thread receives the 'app' instance
    server_thread = threading.Thread(target=startServer, args=(app,))
    server_thread.start()
    app.protocol("WM_DELETE_WINDOW", app.onClosing)
    app.mainloop()
