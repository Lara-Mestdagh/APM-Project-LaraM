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
sockets_list = []       # List of sockets for select
clients = {}            # Dictionary to store client sockets and addresses

# Temporary user credentials for testing
# TODO: later will be reading a hashed and salted file
user_credentials = {
    'user': 'root'  # username is 'user' and password is 'root'
}

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
    global server_socket, server_thread, server_running, sockets_list
    if not server_running:                  # Check if the server is not already running
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Create a new server socket
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     # Set socket options to allow reuse of the address
        server_socket.bind((HOST, PORT))                            # Bind the socket to the host and port
        server_socket.listen()                                      # Start listening for incoming connections
        sockets_list = [server_socket]                              # Reset sockets list to only contain the server socket

        server_running = True           # Set the server running flag to True
        server_thread = threading.Thread(target=accept_connections)     # Create a new thread to accept incoming connections
        server_thread.start()                                           # Start the server thread
        update_server_status("Running")                                 # Update the server status label 
        logging.info("Server started successfully")                     # Log the successful start of the server

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

def update_clients_display():
    global clients_frame
    for widget in clients_frame.winfo_children():
        widget.destroy()  # Clear existing client displays
    for client_id in clients.values():
        label = ctk.CTkLabel(master=clients_frame, text=client_id)
        label.pack()

def add_client(client_socket, client_address):
    client_count = len(clients) + 1
    client_id = f"Client {client_count}: {client_address[0]}"  # Create a unique identifier
    clients[client_socket] = client_id
    update_clients_display()
    logging.info(f"Added new client {client_id}")

def remove_client(client_socket):
    if client_socket in clients:
        logging.info(f"Disconnected {clients[client_socket]}")
        del clients[client_socket]
        update_clients_display()  # Update display after removing client

def accept_connections():
    global server_socket, server_running, sockets_list
    try:
        while server_running:       # Loop while the server is running
            # Use select to check for incoming connections
            read_sockets, _, _ = select.select(sockets_list, [], [], 1)
            for notified_socket in read_sockets:    # Loop through the sockets that are ready to read
                if notified_socket == server_socket:    # If the server socket is ready to read, accept the connection
                    try:
                        # Accept the connection and add the new client socket to the sockets list
                        client_socket, client_address = server_socket.accept()
                        sockets_list.append(client_socket)
                        # next update the GUI to show the connected clients
                        add_client(client_socket, client_address)
                        logging.info(f"Connection from {client_address}")
                    except socket.error as e:
                        logging.error(f"Accept failed: {e}")
                else: 
                    try:  
                        # If the socket is not the server socket, receive the message
                        message = receive_message(notified_socket)
                        # If the message is not None, broadcast it to all clients
                        if message:
                            broadcast_message(message, notified_socket)
                    except Exception as e:
                        logging.error(f"Error processing message from {notified_socket}: {e}")
                        continue  
    except Exception as e:
        logging.error(f"Error in accept_connections: {e}")
        stop_server()

def receive_message(client_socket):
    try:
        # Receive the message from the client
        header = client_socket.recv(4)
        if not header:  # If the header is empty, the connection is closed
            return None  # Connection closed
        message_length = int.from_bytes(header, 'big')  # Get the message length from the header
        full_message = b''                        # Initialize the full message as an empty byte string
        while len(full_message) < message_length:
            # Loop until the full message is received
            packet = client_socket.recv(message_length - len(full_message))
            if not packet:
                return None  # Connection closed
            full_message += packet
        # Deserialize the message data from the full message
        message_data = pickle.loads(full_message)

        # Here we handle the login message type directly
        if message_data.get('type') == 'login':
            handle_login(client_socket, message_data)
        if message_data.get('type') == 'logout':
            handle_logout(client_socket, message_data)
        elif message_data.get('type') == 'register':
            handle_register(client_socket, message_data)
        elif message_data.get('type') == 'broadcast':
            broadcast_message(message_data)
        # Additional message types can be added here as elif clauses

        return message_data  # This ensures we continue receiving other messages
    except Exception as e:
        logging.error(f"Receive error: {e}")
        return None
    
def handle_login(client_socket, message_data):
    username = message_data.get('username')
    password = message_data.get('password')
    if username in user_credentials and user_credentials[username] == password:
        send_message(client_socket, {'type': 'login_response', 'status': 'success', 'message': 'Login successful'})
        logging.info(f"User {username} logged in successfully.")
    else:
        send_message(client_socket, {'type': 'login_response', 'status': 'failure', 'message': 'Invalid username or password'})
        logging.info(f"Failed login attempt for {username}.")

def handle_logout(client_socket, message_data):
    username = message_data.get('username')
    logging.info(f"User {username} logged out successfully.")
    send_message(client_socket, {'type': 'logout_response', 'status': 'success', 'message': 'Logout successful'})

def handle_register(client_socket, message_data):
    username = message_data.get('username')
    password = message_data.get('password')
    if username in user_credentials:
        send_message(client_socket, {'type': 'register_response', 'status': 'failure', 'message': 'Username already exists'})
        logging.info(f"Failed registration attempt for {username}.")
    else:
        user_credentials[username] = password
        send_message(client_socket, {'type': 'register_response', 'status': 'success', 'message': 'Registration successful'})
        logging.info(f"User {username} registered successfully.")

def on_send():
    # Handle the send message button click event
    message = message_input.get().strip()
    if message:
        # Format the message with a 'Server' prefix and send it
        formatted_message = f"Server: {message}"
        broadcast_message(formatted_message)
        display_message(formatted_message)
        message_input.delete(0, 'end')

def broadcast_message(message, sender_socket=None):
    # Broadcast the message to all clients except the sender
    for client_socket in clients:
        if client_socket != sender_socket:
            send_message(client_socket, message)

def send_message(client_socket, message):
    # Send a message to a specific client
    try:
        # Serialize the message and prepend the message length
        serialized_message = pickle.dumps(message)
        # Prepend the message length to the message
        message_header = len(serialized_message).to_bytes(4, 'big')
        # Send the message with the header
        client_socket.sendall(message_header + serialized_message)
    except Exception as e:
        logging.error(f"Send error: {e}")

def display_message(message):
    # Display a message in the message display textbox
    message_display.configure(state='normal')
    message_display.insert('end', message + '\n')
    message_display.configure(state='disabled')
    message_display.see('end')

if __name__ == "__main__":
    try:
        app = create_server_gui()       # Create the server GUI
        app.mainloop()                  # Start the GUI main loop
    except Exception as e:
        logging.error(f"Failed to start the GUI: {e}")