import customtkinter as ctk
from tkinter import messagebox
import pickle
import socket
import tkinter.messagebox as msgbox
import queue
import datetime
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import threading

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
# Setup logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

HOST = "localhost"
PORT = 5000
message_queue = queue.Queue()

app = ctk.CTk()
app.title("Application")
app.geometry("450x400")

def clear_window():
    for widget in app.winfo_children():
        widget.destroy()

def listen_for_server_messages():
    global connected
    try:
        while connected:
            try:
                data = client_socket.recv(1024)
                if not data:
                    raise ConnectionError("Server closed the connection")
                data = pickle.loads(data)
                app.after(0, handle_server_message, data)
            except Exception as e:
                logging.error(f"Failed to receive message: {e}")
                connected = False
                app.after(0, handle_connection_error, e)
                break
    except ConnectionError as e:
        logging.error(f"Connection lost: {e}")
        connected = False

def handle_server_message(data):
    global username, species, personality, hobby
    # Process server message here, update GUI or handle data
    # remember the message is already deserialized
    print("Received data:", data)
    if 'type' in data:
        # depending on the type of data, handle it accordingly
        if data['type'] == "login_response":                        # handle login response here
            # check if the response is successful
            if data['data']['status'] == "success":                 # login successful
                print("Login successful")
                # get the username from the data
                username = data['data']['message'].split()[-1]
                show_dashboard()
            else:
                print("Login failed")
                messagebox.showwarning("Login Failed", data['data']['message'])             # Login failed
        elif data['type'] == "register_response":                   # handle register response here
            if data['data']['status'] == "success":
                print("Registration successful")                    
                messagebox.showinfo("Registration Successful", data['data']['message'])     # Registration successful
                show_login()
            else:
                print("Registration failed")
                # get the message of why the registration failed and send a warning message screen
                messagebox.showwarning("Registration Failed", data['data']['message'])      # Registration failed
        elif data['type'] == "data_parameters":                    # handle data parameters here    
            # we need these for our dropdowns for the search villagers request
            species = data['data']['columns_values']['Species']
            personality = data['data']['columns_values']['Personality']
            hobby = data['data']['columns_values']['Hobby']
    else:
        logging.error("Invalid message type received from server.")
        return

def handle_connection_error(e):
    logging.error(f"Connection error: {e}")
    msgbox.showerror("Connection Error", f"Error communicating with the server: {e}")
    show_retry_connection()

def create_connection():
    global client_socket, connected
    if not connected:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((HOST, PORT))
            client_socket.settimeout(None)  # Optional
            connected = True
            show_login()
            logging.info("Connected to the server successfully.")
            # Start listening thread
            threading.Thread(target=listen_for_server_messages, daemon=True).start()
        except socket.error as e:
            logging.error(f"Failed to connect to the server: {e}")
            client_socket.close()
            connected = False
            show_retry_connection()

def show_retry_connection():
    clear_window()
    title = ctk.CTkLabel(master=app, text="Connection Error")
    title.pack(pady=10)

    message = ctk.CTkLabel(master=app, text="Failed to connect to the server. Trying again...")
    message.pack(pady=10)

    retry_button = ctk.CTkButton(master=app, text="Retry Connection", command=create_connection)
    retry_button.pack(pady=20)

    back_button = ctk.CTkButton(master=app, text="Exit", command=app.quit)
    back_button.pack(pady=10)

def send_request(request_type, data):
    global connected
    if connected:
        try:
            request = {"type": request_type, "data": data}
            client_socket.send(pickle.dumps(request))
            logging.info("Request sent successfully.")
        except socket.error as e:
            logging.error(f"Socket error: {e}")
            connected = False
            create_connection()  # Attempt to reconnect
    else:
        logging.error("Socket is not connected.")
        create_connection()  # Attempt to reconnect

def send_message_and_clear():
    global message_input
    message = message_input.get()  # Get the message from the input field
    if message.strip():  # Ensure the message is not just empty spaces
        send_request("message", message)
        message_input.delete(0, "end")  # Clear the input field after sending the message

def show_dashboard():
    global message_display, message_input, username, request1_dropdown, request3_dropdown
    global request4_species, request4_personality, request4_hobby, species, personality, hobby
    clear_window()
    app.geometry("1000x750")
    title = ctk.CTkLabel(master=app, text=f"Dashboard - {username}", font=("Arial", 16, "bold"))
    title.pack(pady=10)

    logout_button = ctk.CTkButton(master=app, text="Logout", command=logout)
    logout_button.pack(pady=10)

    # GUI elements for requests
    # frame for the requests
    requests_frame = ctk.CTkFrame(master=app)
    requests_frame.pack(pady=10, fill="both", expand=True)

    # request 1
    request1_frame = ctk.CTkFrame(master=requests_frame)
    request1_frame.pack(pady=10, fill="both", expand=True)
    
    # Graph all villagers by race, personality, and hobby.
    # use a button to trigger the request and have a dropdown to select the type of graph
    request1_label = ctk.CTkLabel(master=request1_frame, text="Graph all villagers by:")
    request1_label.pack(side="left", padx=10)

    request1_dropdown = ctk.CTkOptionMenu(master=request1_frame, values=["Species", "Gender", "Personality", "Hobby"])
    request1_dropdown.pack(side="left", padx=10) 

    request1_button = ctk.CTkButton(master=request1_frame, text="Graph", command=handle_request1)
    request1_button.pack(side="right", padx=10)

    # - Graph showing all catchphrases by beginning letter, amount of words, and amount of letters.
    # request 3
    request3_frame = ctk.CTkFrame(master=requests_frame)
    request3_frame.pack(pady=10, fill="both", expand=True)

    request3_label = ctk.CTkLabel(master=request3_frame, text="Graph showing all catchphrases by:")
    request3_label.pack(side="left", padx=10)

    request3_dropdown = ctk.CTkOptionMenu(master=request3_frame, values=["Starting letter", "Word count", "Letter count"])
    request3_dropdown.pack(side="left", padx=10)

    request3_button = ctk.CTkButton(master=request3_frame, text="Graph", command=handle_request3)
    request3_button.pack(side="right", padx=10)

    # - Show the amount of birthdays per month.
    # request 2
    request2_frame = ctk.CTkFrame(master=requests_frame)
    request2_frame.pack(pady=10, fill="both", expand=True)

    request2_label = ctk.CTkLabel(master=request2_frame, text="Graph the amount of birthdays per month.")
    request2_label.pack(side="left", padx=10)

    request2_button = ctk.CTkButton(master=request2_frame, text="Graph", command=handle_request2)
    request2_button.pack(side="right", padx=10)

    # - Search all villagers by filtering by race, personality, birthday, and hobby.
    # use a dropdown to select race, personality, and hobby, if left blank, show all villagers for that category
    # use a date picker to select the birthday, if left blank, show all villagers
    # request 4
    request4_frame = ctk.CTkFrame(master=requests_frame)
    request4_frame.pack(pady=10, fill="both", expand=True)

    request4_label = ctk.CTkLabel(master=request4_frame, text="Search all villagers by:")
    request4_label.pack(side="left", padx=10)

    # using global variables to store the possible values for the columns
    # species, personality, and hobby
    request4_species = ctk.CTkOptionMenu(master=request4_frame, values=species)
    request4_species.pack(side="left", padx=10)

    request4_personality = ctk.CTkOptionMenu(master=request4_frame, values=personality)
    request4_personality.pack(side="left", padx=10)

    request4_hobby = ctk.CTkOptionMenu(master=request4_frame, values=hobby)
    request4_hobby.pack(side="left", padx=10)

    request4_button = ctk.CTkButton(master=request4_frame, text="Search", command=handle_request4)
    request4_button.pack(side="right", padx=10)


    message_input = ctk.CTkEntry(master=app)
    message_input.pack(pady=10, fill="x", padx=10)

    send_button = ctk.CTkButton(master=app, text="Send Message", command=send_message_and_clear)
    send_button.pack(pady=10)

    message_display = ctk.CTkTextbox(master=app, state="normal", height=10)
    message_display.pack(pady=20, fill="both", expand=True)

def handle_data_parameters(data):
    global species, personality, hobby
    # print(data)

    # get the possible values for the columns species, personality, and hobby
    species = data[1].get("Species", [])
    personality = data[1].get("Personality", [])
    hobby = data[1].get("Hobby", [])

    # prepend an empty string to the list of species, personality, and hobby
    species = np.insert(species, 0, "")
    personality = np.insert(personality, 0, "")
    hobby = np.insert(hobby, 0, "")

def show_bar_graph1(graph_data):
    # Get the type of data the graph is displaying for the title
    data_type = graph_data.index.name
    # Create a bar plot of the data
    graph_data.plot(kind='barh', color=['blue'])  # Switched to 'barh' for horizontal bar plot
    plt.title(f'Visual Representation of Villager by {data_type}')
    plt.xlabel("Number of Villagers")
    plt.ylabel(data_type)
    plt.show()

def show_bar_graph2(graph_data):
    # Get the names of the months
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    # Set the y-axis labels to be the names of the months
    graph_data.index = months

    graph_data.plot(kind='barh', color=['blue'])  
    plt.title('Birthdays per Month')
    plt.xlabel('Count')
    plt.ylabel('Month')
    plt.show()

def show_bar_graph3(graph_data, title):
    # Graphs showing all catchphrases by beginning letter, amount of words, and amount of letters.
    data = graph_data

    # Create a bar plot of the data
    if title == "Starting letter":
        data.plot(kind='barh', color=['blue'])
        plt.title('Catchphrases by beginning letter')
        plt.xlabel('Amount')
        plt.ylabel('Letter')
        plt.show()
    elif title == "Word count":
        data.plot(kind='barh', color=['blue'])
        plt.title('Catchphrases by amount of words')
        plt.xlabel('Amount')
        plt.ylabel('Amount of words')
        plt.show()
    elif title == "Letter count":
        data.plot(kind='barh', color=['blue'])
        plt.title('Catchphrases by amount of letters')
        plt.xlabel('Amount')
        plt.ylabel('Amount of letters')
        plt.show()

def show_village_results(results):
    # Create the top-level window
    table_result_window = ctk.CTkToplevel(app)
    table_result_window.title("Search Results")
    table_result_window.geometry("800x400")

    # Create a scrollable frame using CTkScrollableFrame
    scrollable_frame = ctk.CTkScrollableFrame(master=table_result_window)
    scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Create header labels
    headers = ["Name", "Species", "Gender", "Personality", "Hobby", "Birthday", "Catchphrase", "Unique Entry ID"]
    for i, header in enumerate(headers):
        header_label = ctk.CTkLabel(master=scrollable_frame, text=header)
        header_label.grid(row=0, column=i, sticky='ew', padx=5, pady=5)

    # Quick check if the results are empty
    if not results:
        no_results_label = ctk.CTkLabel(master=scrollable_frame, text="No results found.")
        no_results_label.grid(row=1, column=0, columnspan=len(headers), sticky='ew', padx=5, pady=5)
        return

    # Populate the table with data
    for row_index, entry in enumerate(results, start=1):
        for col_index, key in enumerate(headers):
            value = entry.get(key, "N/A")  # Handle missing keys gracefully
            if key == "Birthday" and value != "N/A":  # Check if the key is 'Birthday' and value is not "N/A"
                if isinstance(value, pd.Timestamp):  # Check if the value is a Timestamp
                    value = value.strftime("%d-%B")  # Format the date to 'dd-mmmm'
                else:
                    try:
                        # Attempt to parse and format if not a Timestamp but is a string
                        date_obj = datetime.datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
                        value = date_obj.strftime("%d-%B")  # Format the date to 'dd-mmmm'
                    except ValueError:
                        value = "Invalid date"  # Handle cases where the date format is wrong

            cell_label = ctk.CTkLabel(master=scrollable_frame, text=value)
            cell_label.grid(row=row_index, column=col_index, sticky='ew', padx=5, pady=5)

    # Button to close the window
    close_button = ctk.CTkButton(table_result_window, text="Close", command=table_result_window.destroy)
    close_button.pack(pady=10)

def handle_request1():
    # get the selected value from the dropdown
    data_type = request1_dropdown.get()
    # send the request to the clienthandler
    send_request("request_bar_graph1", data_type)
    logging.info(f"Graph request sent, type {data_type}")

def handle_request2():
    # send the request to the clienthandler
    send_request("request_bar_graph2", "Birthday")
    logging.info(f"Graph request sent, type Birthday")

def handle_request3():
    # get the selected value from the dropdown
    data_type = request3_dropdown.get()
    # send the request to the clienthandler
    send_request("request_bar_graph3", data_type)
    logging.info(f"Graph request sent, type {data_type}")

def handle_request4():
    # get species, name, birthday, personality, and hobby from the dropdowns and date picker
    # check if the values are empty strings and replace them with None
    species = request4_species.get() if request4_species.get() != "" else None
    personality = request4_personality.get() if request4_personality.get() != "" else None
    hobby = request4_hobby.get() if request4_hobby.get() != "" else None

    # send the request to the clienthandler
    send_request("request_search_villagers", {"species": species, "personality": personality, "hobby": hobby})
    logging.info(f"Search request sent, species: {species}, personality: {personality}, hobby: {hobby}")

def update_gui():
    global message_display, username
    while not message_queue.empty():
        try:
            entry = message_queue.get_nowait()
            command = entry[0]  # Always expect the first element to be the command
            # The rest are arguments, if any
            args = entry[1:] if len(entry) > 1 else []

            if command == "show_dashboard":
                username = args[0].split()[-1] if args else "Unknown"
                show_dashboard()
            elif command == "login_failed":
                msgbox.showwarning("Login Failed", args[0] if args else "Unknown error")
            elif command == "connection_error":
                show_retry_connection()
            elif command == "connection_success":
                print("Connection to server successful.")
            elif command == "connection_closed":
                print("Connection to server closed.")
            elif command == "show_login":
                show_login()
            elif command == "login_failed":
                logging.error(f"Login failed: {args[0] if args else 'No data provided'}")
            elif command == "data_parameters":
                print("Data parameters received")
                handle_data_parameters(args[0] if args else {})
                print(args[0] if args else "No data")
            elif command == "graph_data":
                print("Graph data received")
            elif command == "display_graph1":
                print("Display graph1")
                show_bar_graph1(args[0] if args else {})
            elif command == "display_graph2":
                print("Display graph2")
                show_bar_graph2(args[0] if args else {})
            elif command == "display_graph3":
                print("Display graph3")
                if len(args) >= 2:
                    show_bar_graph3(args[0], args[1])
                else:
                    logging.error("Not enough data provided for graph3")
            elif command == "display_search_results":
                print("Display search villagers")
                results = args[0] if args else {}
                show_village_results(results)
            elif command == "message":
                show_message(f"server: {args[0] if args else 'No message'}")
            else:
                logging.error(f"Unhandled command in client: {command}")
        except ValueError as e:
            logging.error(f"Queue message unpacking error in client: {e}")
        except Exception as e:
            logging.error(f"General error processing GUI update in client: {e}")
    app.after(100, update_gui)

def logout():
    send_request("user_logout", "")
    show_login()

def show_message(message):
    global message_display
    # check if contains WARNING
    if "WARNING" in message:
        # remove the WARNING from the message
        message = message.replace("WARNING", "")
        msgbox.showwarning("Warning", message)
    else:
        message_display.insert("end", message + "\n")
        message_display.see("end")

def show_login():
    clear_window()
    title = ctk.CTkLabel(master=app, text="Login")
    title.pack(pady=10)

    username_entry = ctk.CTkEntry(master=app, placeholder_text="Username")
    username_entry.pack(pady=10)
    username_entry.focus_set()  # Set focus to the username entry

    password_entry = ctk.CTkEntry(master=app, placeholder_text="Password", show="*")
    password_entry.pack(pady=10)

    def on_enter_key(event=None):
        send_request("user_login", {"username": username_entry.get(), "password": password_entry.get()})

    app.bind("<Return>", on_enter_key)  # Bind the Enter key to the login action

    login_button = ctk.CTkButton(master=app, text="Login", command=on_enter_key)
    login_button.pack(pady=10)

    register_button = ctk.CTkButton(master=app, text="Register", command=show_register)
    register_button.pack(pady=10)

def show_register():
    clear_window()
    title = ctk.CTkLabel(master=app, text="Register")
    title.pack(pady=10)

    name_entry = ctk.CTkEntry(master=app, placeholder_text="Name")
    name_entry.pack(pady=10)

    username_entry = ctk.CTkEntry(master=app, placeholder_text="Username")
    username_entry.pack(pady=10)

    email_entry = ctk.CTkEntry(master=app, placeholder_text="Email")
    email_entry.pack(pady=10)

    password_entry = ctk.CTkEntry(master=app, placeholder_text="Password", show="*")
    password_entry.pack(pady=10)

    def request_register():
        send_request("user_register", {"name": name_entry.get(), "username": username_entry.get(), "email": email_entry.get(), "password": password_entry.get()})

    register_button = ctk.CTkButton(master=app, text="Register", command=request_register)
    register_button.pack(pady=10)

    back_button = ctk.CTkButton(master=app, text="Back", command=show_login)
    back_button.pack(pady=10)

app.after(100, create_connection)  # Start by checking the connection
app.after(100, update_gui)  # Start the GUI update loop
app.mainloop()