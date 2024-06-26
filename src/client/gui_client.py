import customtkinter as ctk
import tkinter.messagebox as msgbox
import queue
import datetime
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from clienthandler import ClientHandler


# Setup logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# global variables for the GUI
HOST = "localhost"
PORT = 5000
message_queue = queue.Queue()

app = ctk.CTk()
app.title("Application")
app.geometry("450x400")


# ==================== GUI Windows ====================
def clear_window():
    for widget in app.winfo_children():
        widget.destroy()


def show_dashboard():
    global message_display, message_input, username, request1_dropdown, request3_dropdown
    global request4_species, request4_personality, request4_hobby
    clear_window()
    app.geometry("1000x750")
    title = ctk.CTkLabel(master=app, text=f"Dashboard - {username}", font=("Arial", 16, "bold"))
    title.pack(pady=10)

    # logout button, makes sure the username is set to None and shows the login window
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

    # - Show the amount of birthdays per month.
    # request 2
    request2_frame = ctk.CTkFrame(master=requests_frame)
    request2_frame.pack(pady=10, fill="both", expand=True)

    request2_label = ctk.CTkLabel(master=request2_frame, text="Graph the amount of birthdays per month.")
    request2_label.pack(side="left", padx=10)

    request2_button = ctk.CTkButton(master=request2_frame, text="Graph", command=handle_request2)
    request2_button.pack(side="right", padx=10)

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


def show_retry_connection():        # Show the retry connection window when the connection to the server fails
    clear_window()
    title = ctk.CTkLabel(master=app, text="Connection Error")
    title.pack(pady=10)

    message = ctk.CTkLabel(master=app, text="Failed to connect to the server. Trying again...")
    message.pack(pady=10)

    # Retry connection button
    retry_button = ctk.CTkButton(master=app, text="Retry Connection", command=attempt_reconnect)
    retry_button.pack(pady=20)

    # Exit button
    back_button = ctk.CTkButton(master=app, text="Exit", command=app.quit)
    back_button.pack(pady=10)


def show_login():
    clear_window()
    title = ctk.CTkLabel(master=app, text="Login")
    title.pack(pady=10)

    username_entry = ctk.CTkEntry(master=app, placeholder_text="Username")
    username_entry.pack(pady=10)
    username_entry.focus_set()  # Set focus to the username entry

    password_entry = ctk.CTkEntry(master=app, placeholder_text="Password", show="*")    # Hide the password
    password_entry.pack(pady=10)

    # Function to trigger login on Enter key
    def on_enter_key(event):
        client_handler.login(username_entry.get(), password_entry.get())  # Trigger login on Enter key
    app.bind("<Return>", on_enter_key)  # Bind the Enter key to the login action

    # Login button
    login_button = ctk.CTkButton(master=app, text="Login", command=lambda: client_handler.login(username_entry.get(), password_entry.get()))
    login_button.pack(pady=10)

    # Register button
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

    password_entry = ctk.CTkEntry(master=app, placeholder_text="Password", show="*")    # Hide the password
    password_entry.pack(pady=10)

    # Function to trigger register on Enter key
    def on_enter_key(event):
        client_handler.register(name_entry.get(), username_entry.get(), email_entry.get(), password_entry.get())
    app.bind("<Return>", on_enter_key)

    # Register button
    register_button = ctk.CTkButton(master=app, text="Register", command=lambda: client_handler.register(name_entry.get(), username_entry.get(), email_entry.get(), password_entry.get()))
    register_button.pack(pady=10)

    # Back button
    back_button = ctk.CTkButton(master=app, text="Back", command=show_login)
    back_button.pack(pady=10)


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
            value = entry.get(key, "N/A")               # Handle missing keys gracefully
            if key == "Birthday" and value != "N/A":    # Check if the key is 'Birthday' and value is not "N/A"
                if isinstance(value, pd.Timestamp):     # Check if the value is a Timestamp
                    value = value.strftime("%d-%B")     # Format the date to 'dd-mmmm'
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


# ==================== Request Functions ====================
def update_gui():
    global message_display, username
    # Check if the message queue is not empty, here we handle all the responses from the server
    while not message_queue.empty():
        try:
            entry = message_queue.get_nowait()
            command = entry[0]                              # Always expect the first element to be the command
            args = entry[1:] if len(entry) > 1 else []      # The rest are arguments, if any

            if command == "show_dashboard":                 # Show the dashboard after successful login
                username = args[0].split()[-1] if args else "Unknown"
                show_dashboard()
            elif command == "login_failed":                 # Show a warning message if login fails
                msgbox.showwarning("Login Failed", args[0] if args else "Unknown error")
            elif command == "connection_error":
                show_retry_connection()
            elif command == "connection_success":           # Show a message if the connection to the server is successful
                print("Connection to server successful.")
            elif command == "connection_closed":            # Show a message if the connection to the server is closed
                print("Connection to server closed.")
            elif command == "show_login":
                show_login()
            elif command == "login_failed":                 # Show a warning message if login fails
                logging.error(f"Login failed: {args[0] if args else 'No data provided'}")
            elif command == "data_parameters":              # Handle the data parameters received from the server
                print("Data parameters received")
                handle_data_parameters(args[0] if args else {})
            elif command == "graph_data":                   # Handle the graph data received from the server
                # TODO: check if runs
                print("7862486545962485624895652148562519621548962512")
                print("Graph data received")
            elif command == "display_graph1":               # Display the first graph
                print("Display graph1")
                show_bar_graph1(args[0] if args else {})
            elif command == "display_graph2":               # Display the second graph
                print("Display graph2")
                show_bar_graph2(args[0] if args else {})
            elif command == "display_graph3":               # Display the third graph
                print("Display graph3")
                if len(args) >= 2:                # Check if there are enough arguments since we need 2 here
                    show_bar_graph3(args[0], args[1])
                else:
                    logging.error("Not enough data provided for graph3")
            elif command == "display_search_results":       # Display the search results
                print("Display search villagers")
                results = args[0] if args else {}
                show_village_results(results)               # Show the search results in a new window
            elif command == "message":
                show_message(f"server: {args[0] if args else 'No message'}")
            else:
                logging.error(f"Unhandled command in client: {command}")
        except ValueError as e:
            logging.error(f"Queue message unpacking error in client: {e}")
        except Exception as e:
            logging.error(f"General error processing GUI update in client: {e}")
    app.after(100, update_gui)


def handle_request1():                  # Handle the request for the first graph
    # get the selected value from the dropdown
    data_type = request1_dropdown.get()
    client_handler.request_bar_graph1(data_type)
    logging.info(f"Graph request sent, type {data_type}")


def handle_request2():                  # Handle the request for the second graph
    client_handler.request_bar_graph2("Birthday")
    logging.info(f"Graph request sent, type Birthday")


def handle_request3():                  # Handle the request for the third graph
    # get the selected value from the dropdown
    data_type = request3_dropdown.get()
    client_handler.request_bar_graph3(data_type)
    logging.info(f"Graph request sent, type {data_type}")


def handle_request4():                  # Handle the request for the search results
    # get species, name, birthday, personality, and hobby from the dropdowns and date picker
    # check if the values are empty strings and replace them with None
    species = request4_species.get() if request4_species.get() != "" else None
    personality = request4_personality.get() if request4_personality.get() != "" else None
    hobby = request4_hobby.get() if request4_hobby.get() != "" else None

    # Do a check to see if at least one of the values is not None
    if species is None and personality is None and hobby is None:
        msgbox.showwarning("Search Error", "Please select at least one search parameter.")
        return

    # send the request to the clienthandler
    client_handler.request_search_villagers(species, personality, hobby)
    logging.info(f"Search request sent, species: {species}, personality: {personality}, hobby: {hobby}")


# ==================== GUI Functions ====================
def attempt_reconnect():
    logging.info("Attempting to reconnect to the server...")
    try:
        client_handler.connect_to_server()      # Attempt to reconnect to the server
        if client_handler.running:              # If server connection is successful, show the login window
            show_login() 
            return
    except Exception as e:
        logging.error(f"Retry failed: {e}")
    logging.error("Failed to connect to the server. Check your network and try again.")


def send_message_and_clear():
    global message_input
    message = message_input.get()               # Get the message from the input field
    if message.strip():                         # Ensure the message is not just empty spaces
        client_handler.send_message(message)  
        message_input.delete(0, "end")          # Clear the input field after sending the message


def logout():
    client_handler.logout()                # Send the logout request to the server
    show_login()


def show_message(message):
    global message_display
    # check if contains WARNING
    if "WARNING" in message:
        # remove the WARNING from the message
        message = message.replace("WARNING", "")
        msgbox.showwarning("Warning", message)      # Show a warning message box
    else:
        message_display.insert("end", message + "\n")       # Insert the message into the message display
        message_display.see("end")                          # Scroll to the end of the message display


def handle_data_parameters(data):
    global species, personality, hobby

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

    # Create a bar plot of the data, depending on the title
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


# ==================== Main ==================== 
client_handler = ClientHandler(HOST, PORT, message_queue)
app.after(100, update_gui)      # Start the GUI update loop
show_login()                    # Show the login window
app.mainloop()                  # Start the main loop