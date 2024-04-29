import socket
import select
import threading
import customtkinter as ctk

HOST = 'localhost'
PORT = 5000

# Create a server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

sockets_list = [server_socket]
clients = {}
client_checkboxes = {}

def accept_connections():
    while True:
        # Use select to monitor sockets for incoming data
        read_sockets, _, _ = select.select(sockets_list, [], [], 0)
        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                # Accept new client connections
                client_socket, client_address = server_socket.accept()
                sockets_list.append(client_socket)
                clients[client_socket] = f"{client_address[0]}:{client_address[1]}"
                update_client_list_display()
            else:
                try:
                    # Receive message from a client
                    message = notified_socket.recv(1024).decode('utf-8')
                    if message:
                        display_message(f"Client {clients[notified_socket]}: {message}")  # Log here when a message is received
                        broadcast_message(f"From {clients[notified_socket]}: {message}", notified_socket)
                    else:
                        # Client disconnected
                        remove_client(notified_socket)
                except Exception as e:
                    print(f"Error handling message from {clients[notified_socket]}: {e}")
                    remove_client(notified_socket)

def add_client_checkbox(client_socket, address):
    # Create a checkbox for each client
    client_frame = ctk.CTkFrame(master=clients_frame)
    checkbox_var = ctk.IntVar()
    checkbox = ctk.CTkCheckBox(master=client_frame, variable=checkbox_var, text=address)
    checkbox.pack(side='left')
    client_frame.pack(fill='x', padx=10, pady=5)
    client_checkboxes[client_socket] = (checkbox, checkbox_var)

def update_client_list_display():
    # Update the client list display
    for widget in clients_frame.winfo_children():
        widget.destroy()
    for client_socket, address in clients.items():
        add_client_checkbox(client_socket, address)

def broadcast_message(message, sender_socket=None):
    # Broadcast a message to all connected clients
    for client_socket, checkbox_info in client_checkboxes.items():
        checkbox, var = checkbox_info
        if var.get() == 1 and client_socket != sender_socket:  # Skip sending the message back to the sender
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                remove_client(client_socket)

def remove_client(client_socket):
    # Remove a client from the server
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    if client_socket in clients:
        del clients[client_socket]
    if client_socket in client_checkboxes:
        client_checkboxes[client_socket][0].master.destroy()
        del client_checkboxes[client_socket]
    client_socket.close()
    update_client_list_display()

def on_send():
    # Handle the send button click event
    message = message_input.get().strip()
    if message:  # Only send if message is not empty
        display_message(f"Server: {message}")  # Log here when server sends a message
        broadcast_message(message)  # Broadcast without additional logging
        message_input.delete(0, ctk.END)

def display_message(message):
    # Display a message in the message display area
    message_display.configure(state='normal')
    message_display.insert(ctk.END, message + '\n')
    message_display.configure(state='disabled')
    message_display.see(ctk.END)

# Create the GUI application
app = ctk.CTk()
app.title("Server")
app.geometry("400x600")

clients_frame = ctk.CTkFrame(master=app)
clients_frame.pack(fill="both", expand=True, padx=20, pady=20)

message_input = ctk.CTkEntry(master=app)
message_input.pack(pady=10, fill="x")

send_button = ctk.CTkButton(master=app, text="Send Message", command=on_send)
send_button.pack(pady=10)

message_display = ctk.CTkTextbox(master=app, state='disabled', height=10)
message_display.pack(pady=20, fill="both", expand=True)

# Start a separate thread to accept client connections
thread = threading.Thread(target=accept_connections)
thread.start()

# Run the GUI application
app.mainloop()
