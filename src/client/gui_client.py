import socket
import select
import threading
import customtkinter as ctk
import hashlib
import pickle
import os

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

    server_status = ctk.CTkLabel(master=app, text="Server Status", fg_color='red', width=120, height=40)
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

# Start server operation
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
        server_status.configure(fg_color='green')
        print("Server started")

def stop_server():
    global server_socket, server_thread, server_running, server_status
    if server_running:
        server_running = False
        if server_socket:
            if server_socket.fileno() != -1:
                try:
                    server_socket.shutdown(socket.SHUT_RDWR)
                    server_socket.close()
                except Exception as e:
                    print(f"Error shutting down the server socket: {e}")
                finally:
                    if server_socket in sockets_list:
                        sockets_list.remove(server_socket)
            server_socket = None
        if server_thread and server_thread.is_alive():
            server_thread.join()
        server_status.configure(fg_color='red')
        print("Server stopped")

def accept_connections():
    global server_running, sockets_list
    while server_running:
        try:
            read_sockets, _, _ = select.select(sockets_list, [], [], 1)
            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    client_socket, client_address = server_socket.accept()
                    sockets_list.append(client_socket)
                    clients[client_socket] = f"{client_address[0]}:{client_address[1]}"
                    update_client_list_display()
                else:
                    process_client_message(notified_socket)
        except Exception as e:
            if server_running:
                print(f"Server accept loop error: {e}")
            else:
                print("Server shutting down.")

def process_client_message(client_socket):
    try:
        message = client_socket.recv(1024)
        if message:
            try:
                message = pickle.loads(message)
                if message['type'] == 'login':
                    handle_login(message, client_socket)
                # Additional message handling logic here
            except pickle.PickleError as e:
                print(f"Pickle error: {e}")
            except KeyError:
                print("Received malformed data.")
        else:
            raise Exception("Client disconnected")
    except Exception as e:
        print(f"Error handling message from {clients[client_socket]}: {e}")
        remove_client(client_socket)

def add_client_checkbox(client_socket, address):
    client_frame = ctk.CTkFrame(master=clients_frame)
    checkbox_var = ctk.IntVar()
    checkbox = ctk.CTkCheckBox(master=client_frame, variable=checkbox_var, text=address)
    checkbox.pack(side='left')
    client_frame.pack(fill='x', padx=10, pady=5)
    client_checkboxes[client_socket] = (checkbox, checkbox_var)

def remove_client(client_socket):
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    if client_socket in clients:
        print(f"Client {clients[client_socket]} has disconnected")
        del clients[client_socket]
    if client_socket in client_checkboxes:
        # Retrieve the checkbox and var, but check for None before using them
        checkbox, var = client_checkboxes.pop(client_socket, (None, None))
        if checkbox and checkbox[0] and checkbox[0].master:
            app.after(0, checkbox[0].master.destroy)
    try:
        client_socket.close()
    except Exception as e:
        print(f"Error closing client socket: {e}")
    update_client_list_display()

def update_client_list_display():
    try:
        for widget in clients_frame.winfo_children():
            widget.destroy()
        for client_socket, address in clients.items():
            try:
                add_client_checkbox(client_socket, address)
            except Exception as e:
                print(f"Error updating client list display for {address}: {e}")
    except Exception as e:
        print(f"Error during updating client list display: {e}")


def broadcast_message(message, sender_socket=None):
    for client_socket, checkbox_info in client_checkboxes.items():
        checkbox, var = checkbox_info
        if var.get() == 1 and client_socket != sender_socket:
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                remove_client(client_socket)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_credentials(username, hashed_password):
    credentials_path = "user_credentials.txt"
    with open(credentials_path, "a") as file:
        file.write(f"{username},{hashed_password}\n")

def load_credentials():
    user_credentials = {}
    credentials_path = "./data/user_credentials.txt"
    if not os.path.exists(credentials_path):
        with open(credentials_path, "w") as file:
            print("Credentials file created.")
    with open(credentials_path, "r") as file:
        for line in file:
            if line.strip():
                username, hashed_pwd = line.strip().split(',', 1)
                user_credentials[username] = hashed_pwd
    return user_credentials

def handle_registration(message, client_socket):
    parts = message.split(',')
    if len(parts) == 5:
        _, name, username, email, password = parts
        if not all([name, username, email, password]):
            client_socket.send("Registration failed: All fields are required".encode('utf-8'))
            return

        hashed_password = hash_password(password)
        if username not in user_credentials:
            user_credentials[username] = hashed_password
            save_credentials(username, hashed_password)
            client_socket.send("Registration successful".encode('utf-8'))
            display_message(f"New registration: {username} ({email})")
        else:
            client_socket.send("Username already taken".encode('utf-8'))
    else:
        client_socket.send("Registration failed: Incorrect message format".encode('utf-8'))

def handle_login(message, client_socket):
    username = message['username']
    password = message['password']
    hashed_password = hash_password(password)
    user_credentials = load_credentials()  # Ensure credentials are always up-to-date

    if username in user_credentials and user_credentials[username] == hashed_password:
        response = {'type': 'login_response', 'message': 'Login successful'}
        client_socket.send(pickle.dumps(response))
        display_message(f"{username} has logged in successfully.")
    # Temporary code to demonstrate the login process with standard user
    elif username == "user" and password == "root":
        response = {'type': 'login_response', 'message': 'Login successful'}
        client_socket.send(pickle.dumps(response))
        display_message(f"{username} has logged in successfully.")
    else:
        response = {'type': 'login_response', 'message': 'Login failed'}
        client_socket.send(pickle.dumps(response))
        display_message(f"Failed login attempt for {username}")

if __name__ == "__main__":
    create_server_gui()
    user_credentials = load_credentials()
    app.mainloop()
