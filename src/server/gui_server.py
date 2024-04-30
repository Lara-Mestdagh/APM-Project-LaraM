import socket
import select
import threading
import customtkinter as ctk
import pickle
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = 'localhost'
PORT = 5000

server_socket = None
server_thread = None
server_running = False
sockets_list = []
clients = {}

def create_server_gui():
    global clients_frame, message_input, message_display, app, server_status
    app = ctk.CTk()
    app.title("Server Control Panel")
    app.geometry("500x600")

    status_frame = ctk.CTkFrame(master=app)
    status_frame.pack(pady=20, fill='x', padx=20)

    server_status = ctk.CTkLabel(
        master=status_frame, 
        text="Server Status: Stopped", 
        fg_color=('white', 'red'),
        width=120, height=40,
        corner_radius=10)
    server_status.pack()

    control_frame = ctk.CTkFrame(master=app)
    control_frame.pack(pady=10, fill='x', padx=20)

    start_button = ctk.CTkButton(master=control_frame, text="Start Server", command=start_server)
    start_button.pack(side='left', padx=20)

    stop_button = ctk.CTkButton(master=control_frame, text="Stop Server", command=stop_server)
    stop_button.pack(side='right', padx=20)

    clients_frame = ctk.CTkFrame(master=app)
    clients_frame.pack(fill="both", expand=True, padx=20)

    message_frame = ctk.CTkFrame(master=app)
    message_frame.pack(fill='x', padx=20, pady=20)

    message_input = ctk.CTkEntry(master=message_frame)
    message_input.pack(side='left', fill='x', expand=True, pady=10)

    send_button = ctk.CTkButton(master=message_frame, text="Send Message", command=on_send)
    send_button.pack(side='left', padx=10)

    display_frame = ctk.CTkFrame(master=app)
    display_frame.pack(fill='both', expand=True, padx=20, pady=10)

    message_display = ctk.CTkTextbox(master=display_frame, state='disabled', height=10)
    message_display.pack(fill='both', expand=True)

    return app

def update_server_status(status):
    global server_status
    color = 'green' if status == "Running" else 'red'
    server_status.configure(text=f"Server Status: {status}", fg_color=('white', color))

def start_server():
    global server_socket, server_thread, server_running, sockets_list
    if not server_running:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        sockets_list = [server_socket]  # Reset sockets list to only contain the server socket

        server_running = True
        server_thread = threading.Thread(target=accept_connections)
        server_thread.start()
        update_server_status("Running")
        logging.info("Server started successfully")

def stop_server():
    global server_socket, server_thread, server_running, sockets_list
    if server_running:
        server_running = False
        close_all_connections()
        update_server_status("Stopped")
        logging.info("Server stopped successfully")

def close_all_connections():
    global server_socket, server_thread, sockets_list
    # Close client sockets
    for client_socket in list(clients.keys()):
        client_socket.close()
        remove_client(client_socket)
    # Close the server socket
    if server_socket:
        server_socket.close()
        server_socket = None  # Ensure server socket is set to None after closing
    sockets_list = []  # Clear the sockets list to avoid selecting closed sockets
    if server_thread and server_thread is not threading.current_thread():
        server_thread.join()
    logging.info("All connections closed.")

def accept_connections():
    global server_socket, server_running, sockets_list
    try:
        while server_running:
            read_sockets, _, _ = select.select(sockets_list, [], [], 1)
            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    client_socket, client_address = server_socket.accept()
                    sockets_list.append(client_socket)
                    clients[client_socket] = client_address
                    logging.info(f"Connection from {client_address}")
                else:
                    message = receive_message(notified_socket)
                    if message is not None:
                        logging.info(f"Message from {clients[notified_socket]}: {message}")
                        broadcast_message(message, notified_socket)
                    else:
                        remove_client(notified_socket)
    except Exception as e:
        logging.error(f"Error in accept_connections: {e}")
        stop_server()

def receive_message(client_socket):
    try:
        header = client_socket.recv(4)
        if not header:
            return None  # Connection closed
        message_length = int.from_bytes(header, 'big')
        message = client_socket.recv(message_length)
        return pickle.loads(message)
    except Exception as e:
        logging.error(f"Receive error: {e}")
        return None

def broadcast_message(message, sender_socket=None):
    for client_socket in clients:
        if client_socket != sender_socket:
            send_message(client_socket, message)

def send_message(client_socket, message):
    try:
        serialized_message = pickle.dumps(message)
        message_header = len(serialized_message).to_bytes(4, 'big')
        client_socket.sendall(message_header + serialized_message)
    except Exception as e:
        logging.error(f"Send error: {e}")
        remove_client(client_socket)

def remove_client(client_socket):
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    if client_socket in clients:
        logging.info(f"Disconnected {clients[client_socket]}")
        del clients[client_socket]
        client_socket.close()

def on_send():
    message = message_input.get().strip()
    if message:
        formatted_message = f"Server: {message}"
        broadcast_message(formatted_message)
        display_message(formatted_message)
        message_input.delete(0, 'end')

def display_message(message):
    message_display.configure(state='normal')
    message_display.insert('end', message + '\n')
    message_display.configure(state='disabled')
    message_display.see('end')

if __name__ == "__main__":
    try:
        app = create_server_gui()
        app.mainloop()
    except Exception as e:
        logging.error(f"Failed to start the GUI: {e}")