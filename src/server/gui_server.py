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
from queue import Queue

from datasetpre import Dataset
from clienthandler import ClientHandler

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

HOST = "localhost"
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
    app.geometry("550x700")

    # Create the server status components
    status_frame = ctk.CTkFrame(master=app)
    status_frame.pack(pady=20, fill="x", padx=20)

    server_status = ctk.CTkLabel(
        master=status_frame, 
        text="Server Status: Stopped", 
        fg_color=("white", "red"),
        width=120, height=40,
        corner_radius=10)
    server_status.pack()

    # Create the server control components
    control_frame = ctk.CTkFrame(master=app)
    control_frame.pack(pady=10, fill="x", padx=20)

    start_button = ctk.CTkButton(master=control_frame, text="Start Server", command=start_server)
    start_button.pack(side="left")

    stop_button = ctk.CTkButton(master=control_frame, text="Stop Server", command=stop_server)
    stop_button.pack(side="right")

    # Create the connected clients display and request details components

    clients_label = ctk.CTkLabel(master=app, text="Connected Clients", font=("Arial", 14, "bold"))
    clients_label.pack(pady=6)

    button_frame = ctk.CTkFrame(master=app)
    button_frame.pack(fill="x", padx=20, pady=10)
    
    details_button = ctk.CTkButton(master=button_frame, text="Get Details", command=request_details)
    details_button.pack(side="right")

    history_button = ctk.CTkButton(master=button_frame, text="Get History", command=request_search_history)
    history_button.pack(side="left")

    clients_frame = ctk.CTkFrame(master=app)
    clients_frame.pack(fill="both", expand=True, padx=20)

    # Create the message input and display components
    message_frame = ctk.CTkFrame(master=app)
    message_frame.pack(fill="x", padx=20, pady=20)

    message_input = ctk.CTkEntry(master=message_frame)
    message_input.pack(side="left", fill="x", expand=True, pady=10)

    send_button = ctk.CTkButton(master=message_frame, text="Send Message", command=on_send)
    send_button.pack(side="left", padx=10)

    warning_button = ctk.CTkButton(master=message_frame, text="Send Warning", command=send_warning)
    warning_button.pack(side="left")

    display_frame = ctk.CTkFrame(master=app)
    display_frame.pack(fill="both", expand=True, padx=20, pady=10)

    message_display = ctk.CTkTextbox(master=display_frame, state="disabled", height=10)
    message_display.pack(fill="both", expand=True)

    return app  # Return the created app object

def update_server_status(status):
    # Update the server status label with the provided status
    global server_status
    # Set the color to green if the server is running, red if stopped
    color = "green" if status == "Running" else "red"
    server_status.configure(text=f"Server Status: {status}", fg_color=("white", color))

def start_server():
    global server_socket, server_thread, server_running, server_status, dataset, message_queue
    if not server_running:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        sockets_list.append(server_socket)

        # Initialize the message queue here
        message_queue = Queue()

        server_running = True
        server_thread = threading.Thread(target=accept_connections)
        server_thread.start()
        server_status.configure(text="Server Status: Running", fg_color="green")
        # Load the dataset when the server starts
        preprocessor = Dataset("./data/Animal_Crossing_Villagers.csv")
        # log the dataset before preprocessing
        logging.info(f"Dataset before preprocessing: {preprocessor.dataset.head().describe()}")
        dataset = preprocessor.preprocess_data()
        # log the dataset after preprocessing
        logging.info(f"Dataset after preprocessing: {preprocessor.dataset.head().describe()}")
        # log the species and personality heatmap
        preprocessor.species_personality_heatmap()
        # dataset = read_dataset()

        logging.info("Server started")

def stop_server():
    global server_socket, server_thread, server_running, server_status
    if server_running:
        server_running = False
        close_all_connections()
        if server_socket:
            server_socket.close()
            server_socket = None
        if server_thread and server_thread.is_alive():
            server_thread.join()
            server_thread = None
        server_status.configure(text="Server Status: Stopped", fg_color="red")
        logging.info("Server stopped")

def accept_connections():
    logging.info("Server accept loop started")
    global server_running, sockets_list, server_socket, message_queue
    while server_running:
        # Check if the server socket is still valid
        if server_socket is None or server_socket.fileno() == -1:
            logging.error("Server socket is not valid or already closed.")
            break
        read_sockets, _, _ = select.select(sockets_list, [], [], 1)
        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                if not server_running:  # Additional check for server running status
                    logging.info("Server is no longer running.")
                    stop_server()    # Stop the server if it's no longer running
                    break
                try:
                    client_socket, client_address = server_socket.accept()
                    logging.info(f"Connection from {client_address[0]}:{client_address[1]}")
                    sockets_list.append(client_socket)
                    # client_thread = threading.Thread(target=handle_client, args=(client_socket,))
                    # client_thread.start()
                    # Correctly initialize ClientHandler with client_socket and other necessary parameters
                    client_handler = ClientHandler(client_socket, client_address, message_queue)

                    # Start the client handler in a new thread
                    threading.Thread(target=client_handler.accept_connections, daemon=True).start()

                    clients[client_socket] = {"username": "Unknown", "address": f"{client_address[0]}:{client_address[1]}"}
                    update_client_list_display()
                except Exception as e:
                    logging.error(f"Error accepting new connection: {e}")

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

def request_details():
    user_credentials = load_credentials()
    selected_clients = [client_socket for client_socket, checkbox_frame in client_checkboxes.items() if checkbox_frame.winfo_children()[0].get() == 1]

    if len(selected_clients) == 0:
        # Show all client credentials
        for username in user_credentials:
            try:
                _, full_name, email = user_credentials[username].split(",", 2)  # Split into three parts, ignoring the username
                logging.info(f"Details for {username}: Full Name: {full_name}, Email: {email}")
            except ValueError:
                logging.warning(f"Data format error for {username}: {user_credentials[username]}")
    else:
        # Show details for selected clients
        for client_socket in selected_clients:
            username = clients[client_socket]["username"]
            if username in user_credentials:
                try:
                    _, full_name, email = user_credentials[username].split(",", 2)  # Ignore the hashed password
                    logging.info(f"Details for {username}: Full Name: {full_name}, Email: {email}")
                except ValueError:
                    logging.warning(f"Data format error for {username}: {user_credentials[username]}")
            else:
                logging.warning(f"No details found for {username}")

def request_search_history():
    # for now log if the request was made for all clients or selected clients
    selected_clients = [client_socket for client_socket, checkbox_frame in client_checkboxes.items() if checkbox_frame.winfo_children()[0].get() == 1]

    if not selected_clients:
        logging.info("Requesting search history for all clients")
    else:
        logging.info(f"Requesting search history for {len(selected_clients)} clients")
        for client_socket in selected_clients:
            username = clients[client_socket]["username"]
            logging.info(f"Requesting search history for {username}")

def on_send():
    global message_input, message_display
    message = message_input.get().strip()
    if message:
        broadcast_message(message)
        message_input.delete(0, ctk.END)

def send_warning():
    global message_input
    # add warning prefix to the message
    message = "WARNING" + message_input.get().strip()
    if message:
        broadcast_message(message, sender_socket=None)
        message_input.delete(0, ctk.END)

def display_message(message):
    message_display.configure(state="normal")
    message_display.insert(ctk.END, message + "\n")
    message_display.configure(state="disabled")
    message_display.see(ctk.END)

def remove_client(client_socket):
    print("Removing client")
    with clients_lock:
        if client_socket in sockets_list:
            sockets_list.remove(client_socket)
        client_info = clients.pop(client_socket, None)
        if client_info:
            logging.info(f"Client {client_info['username']} at {client_info['address']} has disconnected")
        if client_socket in client_checkboxes:
            checkbox_frame = client_checkboxes.pop(client_socket)
            checkbox_frame.destroy()
        client_socket.close()
    update_client_list_display()

def update_client_list_display():
    for widget in clients_frame.winfo_children():
        widget.destroy()
    for client_socket in clients:
        username = clients[client_socket]["username"]
        ip_address = clients[client_socket]["address"]
        add_client_checkbox(client_socket, username, ip_address)
        # if client is connected, send the parameters to the client
        handle_request_data_parameters(client_socket)

def add_client_checkbox(client_socket, username, ip_address):
    list_text = f"{username} - ({ip_address})"
    client_frame = ctk.CTkFrame(master=clients_frame)
    checkbox_var = ctk.IntVar()
    checkbox = ctk.CTkCheckBox(master=client_frame, variable=checkbox_var, text=list_text)
    checkbox.pack(side="left")
    client_frame.pack(fill="x", padx=10, pady=5)
    client_checkboxes[client_socket] = client_frame

def broadcast_message(message, sender_socket=None):
    # Serialize the message only once for efficiency
    serialized_message = pickle.dumps(message)

    for client_socket, checkbox_frame in client_checkboxes.items():
        # The first child of checkbox_frame should be the CTkCheckBox itself
        checkbox = checkbox_frame.winfo_children()[0]
        if checkbox.winfo_exists():  # Check if the widget still exists before interaction
            if checkbox.get() == 1:  # Check if checkbox is selected
                try:
                    client_socket.send(serialized_message)
                except Exception as e:
                    logging.error(f"Error sending message to {clients[client_socket]["username"]}: {e}")
                    remove_client(client_socket)

if __name__ == "__main__":
    try:
        app = create_server_gui()       # Create the server GUI
        app.mainloop()                  # Start the GUI main loop
    except Exception as e:
        logging.error(f"Failed to start the GUI: {e}")