import socket
import select
import threading
from threading import Lock
import customtkinter as ctk
import hashlib
import pickle
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import math


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
clients_lock = Lock()

def create_server_gui():
    global clients_frame, message_input, message_display, app, server_status
    app = ctk.CTk()
    app.title("Server Control Panel")
    app.geometry("500x600")

    # Create the server status components
    status_frame = ctk.CTkFrame(master=app)
    status_frame.pack(pady=20, fill='x', padx=20)

    server_status = ctk.CTkLabel(
        master=status_frame, 
        text="Server Status: Stopped", 
        fg_color=('white', 'red'),
        width=120, height=40,
        corner_radius=10)
    server_status.pack()

    # Create the server control components
    control_frame = ctk.CTkFrame(master=app)
    control_frame.pack(pady=10, fill='x', padx=20)

    start_button = ctk.CTkButton(master=control_frame, text="Start Server", command=start_server)
    start_button.pack(side='left', padx=10)

    stop_button = ctk.CTkButton(master=control_frame, text="Stop Server", command=stop_server)
    stop_button.pack(side='right', padx=10)

    # Create the connected clients display
    clients_frame = ctk.CTkFrame(master=app)
    clients_frame.pack(fill="both", expand=True, padx=20)

    # TODO: add button for each connected client to get details and search history

    # Create the message input and display components
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

    return app  # Return the created app object

def update_server_status(status):
    # Update the server status label with the provided status
    global server_status
    # Set the color to green if the server is running, red if stopped
    color = 'green' if status == "Running" else 'red'
    server_status.configure(text=f"Server Status: {status}", fg_color=('white', color))

def start_server():
    global server_socket, server_thread, server_running, server_status, dataset
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
        # Load the dataset when the server starts
        dataset = read_dataset()

        logging.info("Server started")

def read_dataset():
    # Load the dataset from the file 
    try:
        dataset = pd.read_csv("./data/Animal_Crossing_Villagers.csv")
        logging.info("Dataset loaded successfully")
        return dataset
    except Exception as e:
        logging.error(f"Error loading dataset: {e}")
        return None

def stop_server():
    global server_socket, server_thread, server_running, server_status
    if server_running:
        server_running = False
        close_all_connections()
        server_status.configure(text="Server Status: Stopped", fg_color='red')
        logging.info("Server stopped")

def accept_connections():
    global server_running, sockets_list
    try:
        while server_running:
            # Check if the server socket is still valid
            if server_socket is None or server_socket.fileno() == -1:
                logging.error("Server socket is not valid or already closed.")
                break
            read_sockets, _, _ = select.select(sockets_list, [], [], 1)
            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    if not server_running:  # Additional check for server running status
                        break
                    try:
                        client_socket, client_address = server_socket.accept()
                        logging.info(f"Connection from {client_address[0]}:{client_address[1]}")
                        sockets_list.append(client_socket)
                        clients[client_socket] = {"username": "Unknown", "address": f"{client_address[0]}:{client_address[1]}"}
                        update_client_list_display()
                    except Exception as e:
                        logging.error(f"Error accepting new connection: {e}")
                else:
                    process_client_message(notified_socket)
    except Exception as e:
        logging.error(f"Server accept loop error: {e}")
    finally:
        logging.info("Server accept loop has ended")

def close_all_connections():
    global server_socket, server_thread
    # Close all client sockets gracefully
    for client_socket in list(clients.keys()):
        try:
            if client_socket.fileno() != -1:  # Check if socket is still open
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
        except Exception as e:
            logging.error(f"Error closing client socket: {e}")
        finally:
            remove_client(client_socket)

    # Now safely close the server socket
    if server_socket and server_socket.fileno() != -1:  # Check if server socket is still open
        try:
            # Additional check if the socket was ever listening
            if server_running:
                server_socket.shutdown(socket.SHUT_RDWR)
        except socket.error as e:
            logging.error(f"Error shutting down the server socket: {e}")
        except Exception as e:
            logging.error(f"General error when shutting down server socket: {e}")
        finally:
            server_socket.close()
            server_socket = None

    if server_thread and server_thread.is_alive():
        server_thread.join()

    logging.info("All connections closed.")

def on_send():
    global message_input, message_display
    message = message_input.get().strip()
    if message:
        broadcast_message(message)
        message_input.delete(0, ctk.END)

def display_message(message):
    message_display.configure(state='normal')
    message_display.insert(ctk.END, message + '\n')
    message_display.configure(state='disabled')
    message_display.see(ctk.END)

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
            # if it not empty, it is a message from the client that should be displayed in the server
            if message:
                display_message(f"{clients[client_socket]['username']}: {message}")
            return
        if not message['type']:
            logging.error("Message format error: 'type' key missing")
            return

        # Process message based on type
        if message['type'] == 'login':
            handle_login(message, client_socket)
        elif message['type'] == 'logout':
            logging.info(f"Client {clients[client_socket]['username']} has logged out")
            # reset the username to 'Unknown' 
            clients[client_socket]["username"] = "Unknown"
            update_client_list_display()
            pass
        elif message['type'] == 'request_data':
            logging.info(f"Client {clients[client_socket]['username']} has requested data")
        elif message['type'] == 'register':
            logging.info(f"Client {clients[client_socket]['username']} has requested to register")
            handle_register(message, client_socket)
        else:
            logging.error(f"Unknown message type: {message['type']}")
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        remove_client(client_socket)

def remove_client(client_socket):
    with clients_lock:
        if client_socket in sockets_list:
            sockets_list.remove(client_socket)
        client_info = clients.pop(client_socket, None)
        if client_info:
            logging.info(f"Client {client_info['username']} at {client_info['address']} has disconnected")
        if client_socket in client_checkboxes:
            checkbox_frame = client_checkboxes.pop(client_socket)
            checkbox_frame.destroy()
    update_client_list_display()

def update_client_list_display():
    for widget in clients_frame.winfo_children():
        widget.destroy()
    for client_socket in clients:
        username = clients[client_socket]["username"]
        ip_address = clients[client_socket]["address"]
        add_client_checkbox(client_socket, username, ip_address)

def add_client_checkbox(client_socket, username, ip_address):
    list_text = f"{username} - ({ip_address})"
    client_frame = ctk.CTkFrame(master=clients_frame)
    checkbox_var = ctk.IntVar()
    checkbox = ctk.CTkCheckBox(master=client_frame, variable=checkbox_var, text=list_text)
    checkbox.pack(side='left')
    client_frame.pack(fill='x', padx=10, pady=5)
    client_checkboxes[client_socket] = client_frame

def broadcast_message(message, sender_socket=None):
    # Serialize the message only once for efficiency
    serialized_message = pickle.dumps(message)

    for client_socket, checkbox_frame in client_checkboxes.items():
        # The first child of checkbox_frame should be the CTkCheckBox itself
        checkbox = checkbox_frame.winfo_children()[0]
        if checkbox.get() == 1:  # Check if checkbox is selected
            try:
                client_socket.send(serialized_message)
            except Exception as e:
                logging.error(f"Error sending message to {clients[client_socket]['username']}: {e}")
                remove_client(client_socket)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
    logging.info(f"Loaded credentials successfully: {user_credentials}")
    return user_credentials

def handle_register(message, client_socket):
    # here we will handle the registration of a new user
    user_credentials = load_credentials()
    name = message['name']
    username = message['username']
    email = message['email']
    password = message['password']

    if username in user_credentials:
        response = {'type': 'register_response', 'status': 'failure', 'message': 'Username already exists'}
        logging.warning(f"Registration attempt denied for {username}: Username already exists.")
    elif len(password) < 4:
        response = {'type': 'register_response', 'status': 'failure', 'message': 'Password must be at least 4 characters'}
        logging.warning(f"Registration attempt denied for {username}: Password too short.")
    elif not email or '@' not in email:
        response = {'type': 'register_response', 'status': 'failure', 'message': 'Invalid email address'}
        logging.warning(f"Registration attempt denied for {username}: Invalid email address.")
    else:
        hashed_password = hash_password(password)
        with open("./data/user_credentials.txt", "a") as file:
            file.write(f"{username},{hashed_password},{name},{email}\n")
        response = {'type': 'register_response', 'status': 'success', 'message': 'Registration successful'}
        logging.info(f"Registration successful for {username}")
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {username}: {e}")


def handle_login(message, client_socket):
    user_credentials = load_credentials()
    username = message['username']
    password = message['password']
    hashed_password = hash_password(password)

    logging.info(f"Login attempt for {username} with password {password}")
    logging.info(f"Hashed password: {hashed_password}")

    if username not in user_credentials:
        response = {'type': 'login_response', 'status': 'failure', 'message': 'Username not found'}
        logging.warning(f"Login attempt denied for {username}: Username not found.")
    elif any(client['username'] == username for client in clients.values()):
        response = {'type': 'login_response', 'status': 'failure', 'message': 'User already logged in'}
        logging.warning(f"Login attempt denied for {username}: User already logged in.")
    else:
        stored_hash = user_credentials[username].split(',')[0]  # Splitting to extract just the hash
        if stored_hash != hashed_password:
            response = {'type': 'login_response', 'status': 'failure', 'message': 'Incorrect password'}
            logging.warning(f"Login attempt denied for {username}: Incorrect password.")
        else:
            clients[client_socket]["username"] = username  # Assuming this part is correctly managed elsewhere
            response = {'type': 'login_response', 'status': 'success', 'message': 'Login successful'}
            logging.info(f"Login successful for {username}")

    try:
        client_socket.send(pickle.dumps(response))
        update_client_list_display()
    except Exception as e:
        logging.error(f"Error sending response to {username}: {e}")

if __name__ == "__main__":
    try:
        app = create_server_gui()       # Create the server GUI
        app.mainloop()                  # Start the GUI main loop
    except Exception as e:
        logging.error(f"Failed to start the GUI: {e}")