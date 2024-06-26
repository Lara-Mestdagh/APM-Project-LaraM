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
from datasetpre import Dataset

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global variables
HOST = "localhost"
PORT = 5000

server_socket = None
server_thread = None
server_running = False
sockets_list = []
clients = {}
client_checkboxes = {}
clients_lock = Lock()
user_credentials = {}
search_history = {}


# ================ GUI Functions ================
def create_server_gui():    
    global clients_frame, message_input, message_display, app, server_status

    # Create the main app window
    app = ctk.CTk()
    app.title("Server Control Panel")
    app.geometry("550x700")

    # Create the server status components------------------------------------------------
    status_frame = ctk.CTkFrame(master=app)
    status_frame.pack(pady=20, fill="x", padx=20)

    # Create the server status label
    server_status = ctk.CTkLabel(
        master=status_frame, 
        text="Server Status: Stopped", 
        fg_color=("white", "red"),
        width=120, height=40,
        corner_radius=10)
    server_status.pack()

    # Create the server control components------------------------------------------------
    control_frame = ctk.CTkFrame(master=app)
    control_frame.pack(pady=10, fill="x", padx=20)

    # start the server button
    start_button = ctk.CTkButton(master=control_frame, text="Start Server", command=start_server)
    start_button.pack(side="left")

    # stop the server button
    stop_button = ctk.CTkButton(master=control_frame, text="Stop Server", command=stop_server)
    stop_button.pack(side="right")

    # Create the connected clients display and request details components-------------------
    clients_label = ctk.CTkLabel(master=app, text="Connected Clients", font=("Arial", 14, "bold"))
    clients_label.pack(pady=6)

    button_frame = ctk.CTkFrame(master=app)
    button_frame.pack(fill="x", padx=20, pady=10)
    
    # request details button
    details_button = ctk.CTkButton(master=button_frame, text="Get Client Details", command=request_details)
    details_button.pack(side="right")

    # request search history button
    history_button = ctk.CTkButton(master=button_frame, text="Get Request History", command=request_search_history)
    history_button.pack(side="left")

    clients_frame = ctk.CTkFrame(master=app)
    clients_frame.pack(fill="both", expand=True, padx=20)

    # Create the message input and display components---------------------------------------
    message_frame = ctk.CTkFrame(master=app)
    message_frame.pack(fill="x", padx=20, pady=20)

    message_input = ctk.CTkEntry(master=message_frame)
    message_input.pack(side="left", fill="x", expand=True, pady=10)

    # send message button
    send_button = ctk.CTkButton(master=message_frame, text="Send Message", command=on_send)
    send_button.pack(side="left", padx=10)

    # send warning button
    warning_button = ctk.CTkButton(master=message_frame, text="Send Warning", command=send_warning)
    warning_button.pack(side="left")

    display_frame = ctk.CTkFrame(master=app)
    display_frame.pack(fill="both", expand=True, padx=20, pady=10)

    message_display = ctk.CTkTextbox(master=display_frame, state="disabled", height=10)
    message_display.pack(fill="both", expand=True)

    return app  # Return the created app object


def show_search_history_in_window(search_data):
    # Create a top-level window
    search_result_window = ctk.CTkToplevel(app)
    search_result_window.title("Search History")
    search_result_window.geometry("500x600")  # Adjust size as needed

    # create a scrollable frame for the search history
    scroll_frame = ctk.CTkScrollableFrame(master=search_result_window)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Loop over the search data and display it in the scrollable frame
    for username, searches in search_data.items():
        # Create a frame for each user
        user_frame = ctk.CTkFrame(master=scroll_frame)
        user_frame.pack(fill="x", pady=5)

        # Create a label for the username with a larger font size
        username_label = ctk.CTkLabel(master=user_frame, text=f"request history of {username}:", font=("Arial", 14, "bold"))
        username_label.pack(anchor="w")

        # Create a label for each search with a smaller font size
        for search in searches:
            search_label = ctk.CTkLabel(master=user_frame, text=f"Name:  - {search}", font=("Arial", 12))
            search_label.pack(anchor="w")

    # add a close button to the window
    close_button = ctk.CTkButton(master=search_result_window, text="Close", command=search_result_window.destroy)
    close_button.pack(pady=10)


def add_client_checkbox(client_socket, username, ip_address):  
    # Add a checkbox for the client to the clients_frame
    list_text = f"{username} - ({ip_address})"
    client_frame = ctk.CTkFrame(master=clients_frame)
    checkbox_var = ctk.IntVar()
    checkbox = ctk.CTkCheckBox(master=client_frame, variable=checkbox_var, text=list_text)
    checkbox.pack(side="left")
    client_frame.pack(fill="x", padx=10, pady=5)
    # log the client and the checkbox for knowing which client is selected
    client_checkboxes[client_socket] = client_frame


def display_message(message):   # Display a message in the message display
    message_display.configure(state="normal")
    message_display.insert(ctk.END, message + "\n")
    message_display.configure(state="disabled")
    message_display.see(ctk.END)


def on_send():
    global message_input
    # get the message from the input field and broadcast it to all clients
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


def update_client_list_display():
    for widget in clients_frame.winfo_children():
        widget.destroy()
    for client_socket in clients:
        username = clients[client_socket]["username"]
        ip_address = clients[client_socket]["address"]
        add_client_checkbox(client_socket, username, ip_address)


# ================= Server Functions ================
def start_server():
    global server_socket, server_thread, server_running, server_status, dataset, user_credentials, search_history

    # check if the server is indeed running
    if not server_running:
        # Create the server socket and start listening for connections
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        sockets_list.append(server_socket)

        # flag the server running as true and start the server thread
        server_running = True
        server_thread = threading.Thread(target=accept_connections)
        server_thread.start()
        server_status.configure(text="Server Status: Running", fg_color="green")

        logging.info("Server started")

        try:
            # Load the dataset when the server starts
            preprocessor = Dataset("./data/Animal_Crossing_Villagers.csv")
            dataset = preprocessor.preprocess_data()
            # get the species and personality heatmap and boxplots
            preprocessor.species_personality_heatmap()
            preprocessor.analyze_boxplots()
        except Exception as e:
            logging.error(f"Error loading dataset: {e}")

        user_credentials = load_credentials()
        search_history = load_search_history()


def stop_server():
    global server_running, server_status
    # check if the server is running
    if server_running:
        # set server running to false and close all connections
        server_running = False          # Set flag to false
        close_all_connections()         # Close all connections
        server_status.configure(text="Server Status: Stopped", fg_color="red")
        logging.info("Server stopped")


def update_server_status(status):
    global server_status
    # Update the server status label with the provided status
    # Set the color to green if the server is running, red if stopped
    color = "green" if status == "Running" else "red"
    server_status.configure(text=f"Server Status: {status}", fg_color=("white", color))


def accept_connections():
    global sockets_list
    try:
        while server_running:
            # Check if the server socket is still valid
            if server_socket is None or server_socket.fileno() == -1:
                logging.error("Server socket is not valid or already closed.")
                break
            # Use select to check for incoming connections
            read_sockets, _, _ = select.select(sockets_list, [], [], 1)
            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    if not server_running:  # Additional check for server running status
                        break
                    try:
                        # Accept new connection
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
        logging.error(f"Server accept loop error: {e} - ending loop")


def close_all_connections():
    # When the server is stopped, we need to close all connections
    global server_socket, server_thread
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


def remove_client(client_socket):
    with clients_lock:
        if client_socket in sockets_list:
            sockets_list.remove(client_socket)
        client_info = clients.pop(client_socket, None)
        if client_info:
            logging.info(f"Client {client_info["username"]} at {client_info["address"]} has disconnected")
        if client_socket in client_checkboxes:
            checkbox_frame = client_checkboxes.pop(client_socket)
            checkbox_frame.destroy()
    update_client_list_display()


def broadcast_message(message, sender_socket=None):
    # Serialize the message only once for efficiency
    serialized_message = pickle.dumps(message)

    # Check if any checkboxes are selected
    selected_clients = [client_socket for client_socket, checkbox_frame in client_checkboxes.items() 
                        if checkbox_frame.winfo_children()[0].winfo_exists() and 
                        checkbox_frame.winfo_children()[0].get() == 1]

    # If no checkboxes are selected, send to all clients
    if not selected_clients:
        selected_clients = list(client_checkboxes.keys())

    # Loop over all selected clients and send the message
    for client_socket in selected_clients:
        try:
            client_socket.send(serialized_message)
        except Exception as e:
            logging.error(f"Error sending message to {clients[client_socket]['username']}: {e}")
            remove_client(client_socket)


# ================= Server Data Functions ================
def request_details():
    # get the selected clients and display their details
    user_credentials = load_credentials()
    selected_clients = [client_socket for client_socket, checkbox_frame in client_checkboxes.items() if checkbox_frame.winfo_children()[0].get() == 1]

    # if no clients are selected, display all client details
    if len(selected_clients) == 0:
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
    global search_history, clients, client_checkboxes
    search_history = load_search_history()

    # Get the selected clients and display their search history
    selected_clients = [client_socket for client_socket, checkbox_frame in client_checkboxes.items() if checkbox_frame.winfo_children()[0].get() == 1]

    search_data_to_display = {}

    try:
        # If no clients are selected, display all search history
        if len(selected_clients) == 0:
            search_data_to_display = search_history
        else:
            # Show search history for selected clients
            for client_socket in selected_clients:
                username = clients[client_socket]["username"]
                if username in search_history:
                    search_data_to_display[username] = search_history[username]
                else:
                    search_data_to_display[username] = ["No search history found"]

        # Display the search history in a CTkToplevel window
        show_search_history_in_window(search_data_to_display)

    except Exception as e:
        logging.error(f"Error processing search history: {e}")


def write_to_search_history(username, search):    
    # Add the search to the search history
    if username in search_history:
        if isinstance(search_history[username], list):
            search_history[username].append(search)
        else:
            search_history[username] = [search]
    else:
        search_history[username] = [search]
    
    # Write the search history to the file
    search_history_path = "./data/search_history.txt"
    try:
        with open(search_history_path, "w") as file:
            for user, searches in search_history.items():
                for each_search in searches:
                    file.write(f"{user},{each_search}\n")
    except IOError as e:
        logging.error(f"Failed to write to file: {e}")

    logging.info(f"Search history updated for {username}")


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
                    username, hashed_pwd = line.strip().split(",", 1)
                    user_credentials[username] = hashed_pwd
    except IOError as e:
        logging.error(f"Failed to read credentials file: {e}")
    return user_credentials


def load_search_history():
    global search_history_path
    search_history_path = "./data/search_history.txt"
    search_history = {}
    try:
        if not os.path.exists(search_history_path):
            with open(search_history_path, "w") as file:
                logging.info("Search history file created.")
        with open(search_history_path, "r") as file:
            for line in file:
                if line.strip():
                    username, search = line.strip().split(",", 1)
                    if username in search_history:
                        search_history[username].append(search)
                    else:
                        search_history[username] = [search]
    except IOError as e:
        logging.error(f"Failed to read search history file: {e}")
    return search_history


# ================= Dataset Data Functions ================
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

        # Check if "type" key exists in the message
        if "type" not in message:
            # if it not empty, it is a message from the client that should be displayed in the server
            if message:
                display_message(f"{clients[client_socket]["username"]}: {message}")
            return
        if not message["type"]:
            logging.error("Message format error: type key missing")
            return

        # Process message based on type
        if message["type"] == "login":
            handle_login(message, client_socket)
        elif message["type"] == "logout":
            logging.info(f"Client {clients[client_socket]["username"]} has logged out")
            # reset the username to "Unknown" 
            clients[client_socket]["username"] = "Unknown"
            update_client_list_display()
            pass
        elif message["type"] == "request_data_parameters":
            logging.info(f"Client {clients[client_socket]["username"]} has requested data parameters")
            handle_request_data_parameters(message, client_socket)
        elif message["type"] == "register":
            logging.info(f"Client {clients[client_socket]["username"]} has requested to register")
            handle_register(message, client_socket)
        elif message["type"] == "request_bar_graph1":
            logging.info(f"Client {clients[client_socket]["username"]} has requested bar graph 1")
            data_type = message["data_type"]
            handle_request_bar_graph1(data_type, client_socket)
            write_to_search_history(clients[client_socket]["username"], "request_bar_graph1")
        elif message["type"] == "request_bar_graph2":
            logging.info(f"Client {clients[client_socket]["username"]} has requested bar graph 2")
            data_type = message["data_type"]
            handle_request_bar_graph2(data_type, client_socket)
            write_to_search_history(clients[client_socket]["username"], "request_bar_graph2")
        elif message["type"] == "request_bar_graph3":
            logging.info(f"Client {clients[client_socket]["username"]} has requested bar graph 3")
            data_type = message["data_type"]
            handle_request_bar_graph3(data_type, client_socket)
            # logging.info(f"Client {clients
            write_to_search_history(clients[client_socket]["username"], "request_bar_graph3")
        elif message["type"] == "request_search_villagers":
            logging.info(f"Client {clients[client_socket]["username"]} has requested to search villagers")
            parameters = message["parameters"]
            handle_request_search_villagers(parameters, client_socket)
            write_to_search_history(clients[client_socket]["username"], "request_search_villagers")
        else:
            logging.error(f"Unknown message type: {message["type"]}")
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        remove_client(client_socket)


def handle_request_bar_graph1(data_type, client_socket):
    # graph data is column name, get the unique values and their counts to send to the client
    global dataset
    if dataset is None:
        response = {"type": "graph", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Graph request denied: Dataset not loaded")
    else:
        try:
            # get the unique values and their counts
            graph_data = dataset[data_type].value_counts()
            response = {"type": "received_graph1", "status": "success", "graph_data": graph_data}
        except Exception as e:
            response = {"type": "received_graph1", "status": "failure", "message": f"Error processing graph data: {e}"}
            logging.error(f"Error processing graph data: {e}")

    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")


def handle_request_bar_graph2(data_type, client_socket):
    global dataset  
    if dataset is None:
        response = {"type": "graph", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Graph request denied: Dataset not loaded")
    else:
        try:
             # Extract the month from the date column
            dataset['Month'] = pd.to_datetime(dataset[data_type]).dt.month
            # Count the number of occurrences of each month
            graph_data = dataset['Month'].value_counts().sort_index()            
            response = {"type": "received_graph2", "status": "success", "graph_data": graph_data}
        except Exception as e:
            response = {"type": "received_graph2", "status": "failure", "message": f"Error processing graph data: {e}"}
            logging.error(f"Error processing graph data: {e}")
    
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")
        

def handle_request_bar_graph3(data_type, client_socket):
    # depending on data_type graph catchphrases by beginning letter, amount of words, and amount of letters.
    global dataset
    if dataset is None:
        response = {"type": "graph", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Graph request denied: Dataset not loaded")
    else:
        try:
            if data_type == "Starting letter":
                # Catchphrases by beginning letter
                catchphrase_dataset = dataset["Catchphrase"].str[0].str.upper()
                catchphrase_letter = catchphrase_dataset.value_counts().sort_index()
                graph_data = catchphrase_letter
            elif data_type == "Word count":
                # Catchphrases by amount of words
                catchphrase_dataset = dataset["Catchphrase"].str.split().str.len()
                catchphrase_words = catchphrase_dataset.value_counts().sort_index()
                graph_data = catchphrase_words
            elif data_type == "Letter count":
                # Catchphrases by amount of letters
                catchphrase_dataset = dataset["Catchphrase"].str.len()
                catchphrase_letters = catchphrase_dataset.value_counts().sort_index()
                graph_data = catchphrase_letters

            response = {"type": "received_graph3", "status": "success", "graph_data": graph_data, "data_type": data_type}
        except Exception as e:
            response = {"type": "received_graph3", "status": "failure", "message": f"Error processing graph data: {e}"}
            logging.error(f"Error processing graph data: {e}")
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")


def handle_request_search_villagers(parameters, client_socket):
    global dataset
    if dataset is None:
        response = {"type": "search_results", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Search request denied: Dataset not loaded")
    else:
        # using species, birthday, personality and hobby let's filter villagers
        # if it is none, it means we don't want to filter by that attribute
        species = parameters.get("species")
        birthday = parameters.get("birthday")
        personality = parameters.get("personality")
        hobby = parameters.get("hobby")
        filtered_data = dataset
        if species:
            filtered_data = filtered_data[filtered_data['Species'] == species]
        if birthday:
            filtered_data = filtered_data[filtered_data['Birthday'].dt.strftime('%b') == birthday]
        if personality:
            filtered_data = filtered_data[filtered_data['Personality'] == personality]
        if hobby:
            filtered_data = filtered_data[filtered_data['Hobby'] == hobby]

        response = {"type": "search_results", "status": "success", "search_results": filtered_data.to_dict(orient="records")}
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")


def handle_request_data_parameters(message, client_socket):
    global dataset
    if dataset is None:
        response = {"type": "data_parameters", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Data parameters request denied: Dataset not loaded")
    else:
        # get the columns and the unique values for species, personality, and hobby
        columns = dataset.columns.tolist()
        species_values = dataset['Species'].unique()
        personality_values = dataset['Personality'].unique()
        hobby_values = dataset['Hobby'].unique()
        # group the values into a dictionary
        columns_values = {
            "Species": species_values,
            "Personality": personality_values,
            "Hobby": hobby_values
        }
        response = {"type": "data_parameters", "status": "success", "columns": columns, "columns_values": columns_values}

    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")
        remove_client(client_socket)


def handle_register(message, client_socket):
    # here we will handle the registration of a new user
    name = message["name"]
    username = message["username"]
    email = message["email"]
    password = message["password"]

    # check if the username already exists
    if username in user_credentials:
        response = {"type": "register_response", "status": "failure", "message": "Username already exists"}
        logging.warning(f"Registration attempt denied for {username}: Username already exists.")
    # check if the password is too short, minimum 4 characters
    elif len(password) < 4:
        response = {"type": "register_response", "status": "failure", "message": "Password must be at least 4 characters"}
        logging.warning(f"Registration attempt denied for {username}: Password too short.")
    # check if the email is valid
    elif not email or "@" not in email:
        response = {"type": "register_response", "status": "failure", "message": "Invalid email address"}
        logging.warning(f"Registration attempt denied for {username}: Invalid email address.")
    # last check to make sure none of the fields are empty or over 32 characters
    elif not all(len(field) <= 32 and field for field in [name, username, email]):
        response = {"type": "register_response", "status": "failure", "message": "Fields must not be empty or over 16 characters"}
        logging.warning(f"Registration attempt denied for {username}: Fields must not be empty or over 16 characters.")
    # if all checks pass, we can register the user
    else:
        hashed_password = hash_password(password)
        with open("./data/user_credentials.txt", "a") as file:
            file.write(f"{username},{hashed_password},{name},{email}\n")
        response = {"type": "register_response", "status": "success", "message": "Registration successful"}
        logging.info(f"Registration successful for {username}")
        # reload the credentials
        user_credentials[username] = hashed_password
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {username}: {e}")


def handle_login(message, client_socket):
    user_credentials = load_credentials()
    username = message["username"]
    password = message["password"]
    hashed_password = hash_password(password)

    if username not in user_credentials:
        response = {"type": "login_response", "status": "failure", "message": "Username not found"}
        logging.warning(f"Login attempt denied for {username}: Username not found.")
    elif any(client["username"] == username for client in clients.values()):
        response = {"type": "login_response", "status": "failure", "message": "User already logged in"}
        logging.warning(f"Login attempt denied for {username}: User already logged in.")
    else:
        stored_hash = user_credentials[username].split(",")[0]  # Splitting to extract just the hash
        if stored_hash != hashed_password:
            response = {"type": "login_response", "status": "failure", "message": "Incorrect password"}
            logging.warning(f"Login attempt denied for {username}: Incorrect password.")
        else:
            clients[client_socket]["username"] = username  # Assuming this part is correctly managed elsewhere
            response = {"type": "login_response", "status": "success", "message": "Login successful for " + username}
            logging.info(f"Login successful for {username}")

    try:
        client_socket.send(pickle.dumps(response))
        update_client_list_display()
    except Exception as e:
        logging.error(f"Error sending response to {username}: {e}")


# ================= Main Function ================
def main():
    try:
        app = create_server_gui()       # Create the server GUI
        app.mainloop()                  # Start the GUI main loop
    except Exception as e:
        logging.error(f"Failed to start the GUI: {e}")

if __name__ == "__main__":
    main()