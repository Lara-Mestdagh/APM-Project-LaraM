import socket
import select
import threading
import customtkinter as ctk
import hashlib
import pickle
import os
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
client_checkboxes = {}

def create_server_gui():
    global clients_frame, message_input, message_display, app, server_status
    app = ctk.CTk()
    app.title("Server Control")
    app.geometry("450x600")

    server_status = ctk.CTkLabel(master=app, text="Server Status: Stopped", fg_color='red', width=140, height=40)
    server_status.pack(pady=20)

    start_button = ctk.CTkButton(master=app, text="Start Server", command=start_server)
    start_button.pack(pady=10)

    stop_button = ctk.CTkButton(master=app, text="Stop Server", command=stop_server)
    stop_button.pack(pady=10)

    clients_frame = ctk.CTkFrame(master=app)
    clients_frame.pack(fill="both", expand=True, padx=20, pady=20)

    message_input = ctk.CTkEntry(master=app)
    message_input.pack(pady=10, fill="x")

    send_button = ctk.CTkButton(master=app, text="Send Message", command=on_send)
    send_button.pack(pady=10)

    message_display = ctk.CTkTextbox(master=app, state='disabled', height=10)
    message_display.pack(pady=20, fill="both", expand=True)

def on_send():
    global message_input, message_display
    message = message_input.get().strip()
    if message:
        display_message(f"Server: {message}")
        broadcast_message(message)
        message_input.delete(0, ctk.END)

def display_message(message):
    message_display.configure(state='normal')
    message_display.insert(ctk.END, message + '\n')
    message_display.configure(state='disabled')
    message_display.see(ctk.END)

def start_server():
    global server_socket, server_thread, server_running, server_status
    if not server_running:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        sockets_list.append(server_socket)

        server_running = True
        server_thread = threading.Thread(target=accept_connections)
        server_thread.start()
        server_status.configure(text="Server Status: Running", fg_color='green')
        logging.info("Server started")

def stop_server():
    global server_socket, server_thread, server_running, server_status
    if server_running:
        server_running = False
        close_all_connections()
        server_status.configure(text="Server Status: Stopped", fg_color='red')
        logging.info("Server stopped")

def close_all_connections():
    global server_socket, server_thread
    # Close all client sockets gracefully
    for client_socket in list(clients.keys()):
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except Exception as e:
            logging.error(f"Error closing client socket: {e}")
        finally:
            remove_client(client_socket)

    # Now safely close the server socket
    if server_socket:
        try:
            server_socket.shutdown(socket.SHUT_RDWR)
            server_socket.close()
        except Exception as e:
            logging.error(f"Error shutting down the server socket: {e}")
        finally:
            server_socket = None

    if server_thread and server_thread.is_alive():
        server_thread.join()

    logging.info("All connections closed.")


def accept_connections():
    global server_running, sockets_list
    try:
        while server_running:
            read_sockets, _, _ = select.select(sockets_list, [], [], 1)
            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    client_socket, client_address = server_socket.accept()
                    logging.info(f"Connection from {client_address[0]}:{client_address[1]}")
                    sockets_list.append(client_socket)
                    clients[client_socket] = f"{client_address[0]}:{client_address[1]}"
                    update_client_list_display()
                else:
                    process_client_message(notified_socket)
    except Exception as e:
        logging.error(f"Server accept loop error: {e}")
    finally:
        logging.info("Server accept loop has ended")

def process_client_message(client_socket):
    try:
        message = client_socket.recv(1024)
        if not message:
            raise Exception("Client disconnected")
        # Attempt to deserialize the message
        try:
            message = pickle.loads(message)
        except pickle.PickleError as e:
            logging.error(f"Pickle error processing message: {e}")
            return

        # Check if 'type' key exists in the message
        if 'type' not in message:
            logging.error("Message format error: 'type' key missing")
            return

        # Process message based on type
        if message['type'] == 'login':
            handle_login(message, client_socket)
        elif message['type'] == 'send_message':
            # Handle other message types
            pass
        else:
            logging.error(f"Unknown message type: {message['type']}")
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        remove_client(client_socket)


def remove_client(client_socket):
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    client_info = clients.pop(client_socket, None)
    if client_info:
        logging.info(f"Client {client_info} has disconnected")
    if client_socket in client_checkboxes:
        checkbox_frame = client_checkboxes.pop(client_socket)
        checkbox_frame.destroy()
    update_client_list_display()

def update_client_list_display():
    for widget in clients_frame.winfo_children():
        widget.destroy()
    for client_socket, address in clients.items():
        add_client_checkbox(client_socket, address)

def add_client_checkbox(client_socket, address):
    client_frame = ctk.CTkFrame(master=clients_frame)
    checkbox_var = ctk.IntVar()
    checkbox = ctk.CTkCheckBox(master=client_frame, variable=checkbox_var, text=address)
    checkbox.pack(side='left')
    client_frame.pack(fill='x', padx=10, pady=5)
    client_checkboxes[client_socket] = client_frame

def broadcast_message(message, sender_socket=None):
    for client_socket in clients:
        if client_socket != sender_socket:
            try:
                logging.debug(f"Sending message: {message} to {clients[client_socket]}")
                client_socket.send(message.encode('utf-8'))
            except Exception as e:
                logging.error(f"Failed to send message to {clients[client_socket]}: {e}")
                remove_client(client_socket)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_credentials(username, hashed_password):
    credentials_path = "user_credentials.txt"
    try:
        with open(credentials_path, "a") as file:
            file.write(f"{username},{hashed_password}\n")
    except IOError as e:
        logging.error(f"Failed to write to credentials file: {e}")

def load_credentials():
    user_credentials = {}
    credentials_path = "./data/user_credentials.txt"
    try:
        if not os.path.exists(credentials_path):
            with open(credentials_path, "w") as file:
                logging.info("Credentials file created.")
        with open(credentials_path, "r") as file:
            for line in file:
                if line.strip():
                    username, hashed_pwd = line.strip().split(',', 1)
                    user_credentials[username] = hashed_pwd
    except IOError as e:
        logging.error(f"Failed to read credentials file: {e}")
    return user_credentials

def handle_login(message, client_socket):
    username = message['username']
    password = message['password']
    hashed_password = hash_password(password)
    user_credentials = load_credentials()

    if username in user_credentials and user_credentials[username] == hashed_password:
        response = {'type': 'login_response', 'status': 'success', 'message': 'Login successful'}
        logging.info(f"{username} has logged in successfully.")
    # standard user with password root for testing TODO CHANGE THIS
    elif username == "user" and password == "root":
        response = {'type': 'login_response', 'status': 'success', 'message': 'Login successful'}
        logging.info(f"{username} has logged in successfully.")
    else:
        response = {'type': 'login_response', 'status': 'failure', 'message': 'Login failed'}
        logging.error(f"Failed login attempt for {username}")
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {username}: {e}")
        remove_client(client_socket)

if __name__ == "__main__":
    create_server_gui()
    user_credentials = load_credentials()
    app.mainloop()


# Error shutting down the server socket: [WinError 10057] A request to send or receive data was disallowed because the socket is not connected and (when sending on a datagram socket using a sendto call) no address was supplied
# happens when server shuts down and a client has connected to it 