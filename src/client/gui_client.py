import customtkinter as ctk
import tkinter.messagebox as msgbox
import queue
import time
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from tkcalendar import Calendar, DateEntry
from ..server.clienthandler import ClientHandler


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

def show_retry_connection():
    clear_window()
    title = ctk.CTkLabel(master=app, text="Connection Error")
    title.pack(pady=10)

    message = ctk.CTkLabel(master=app, text="Failed to connect to the server. Trying again...")
    message.pack(pady=10)

    retry_button = ctk.CTkButton(master=app, text="Retry Connection", command=attempt_reconnect)
    retry_button.pack(pady=20)

    back_button = ctk.CTkButton(master=app, text="Exit", command=app.quit)
    back_button.pack(pady=10)

def attempt_reconnect():
    logging.info("Attempting to reconnect to the server...")
    try:
        client_handler.connect_to_server()
        if client_handler.running:
            show_login() 
            return
    except Exception as e:
        logging.error(f"Retry failed: {e}")
    logging.error("Failed to connect to the server. Check your network and try again.")

def send_message_and_clear():
    global message_input
    message = message_input.get()  # Get the message from the input field
    if message.strip():  # Ensure the message is not just empty spaces
        client_handler.send_message(message)  # Send the message using the ClientHandler
        message_input.delete(0, "end")  # Clear the input field after sending the message

def show_dashboard():
    global message_display, message_input, username, request1_dropdown, request3_dropdown
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
    request4_race = ctk.CTkOptionMenu(master=request4_frame, values=species)
    request4_race.pack(side="left", padx=10)

    # for birthday, we can use a date picker
    request4_birthday = DateEntry(request4_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
    request4_birthday.pack(side="left", padx=10)

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
    print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
    print(graph_data)
    # Graphs showing all catchphrases by beginning letter, amount of words, and amount of letters.
    data = graph_data

    # Create a bar plot of the data
    if title == "Starting letter":
        print("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
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

def handle_request1():
    # get the selected value from the dropdown
    data_type = request1_dropdown.get()
    # send the request to the clienthandler
    # client_handler.send_message({"type": "request_graph", "data_type": data_type})
    client_handler.request_bar_graph1(data_type)
    logging.info(f"Graph request sent, type {data_type}")

def handle_request2():
    # send the request to the clienthandler
    # client_handler.send_message({"type": "request_graph", "data_type": "Birthday"})
    client_handler.request_bar_graph2("Birthday")
    logging.info(f"Graph request sent, type Birthday")

def handle_request3():
    # get the selected value from the dropdown
    data_type = request3_dropdown.get()
    # send the request to the clienthandler
    client_handler.request_bar_graph3(data_type)
    logging.info(f"Graph request sent, type {data_type}")

def handle_request4():
    print("Request 4")

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
    client_handler.logout()
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

    def on_enter_key(event):
        client_handler.login(username_entry.get(), password_entry.get())  # Trigger login on Enter key
    app.bind("<Return>", on_enter_key)  # Bind the Enter key to the login action

    login_button = ctk.CTkButton(master=app, text="Login", command=lambda: client_handler.login(username_entry.get(), password_entry.get()))
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

    register_button = ctk.CTkButton(master=app, text="Register", command=lambda: client_handler.register(name_entry.get(), username_entry.get(), email_entry.get(), password_entry.get()))
    register_button.pack(pady=10)

    back_button = ctk.CTkButton(master=app, text="Back", command=show_login)
    back_button.pack(pady=10)
    
client_handler = ClientHandler(HOST, PORT, message_queue)
app.after(100, update_gui)
show_login()
app.mainloop()
