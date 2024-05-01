import customtkinter as ctk
import tkinter.messagebox as msgbox
import queue
import time
import logging
import pandas as pd
import matplotlib.pyplot as plt

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
    global message_display, message_input, username, request1_dropdown
    clear_window()
    app.geometry("700x650")
    title = ctk.CTkLabel(master=app, text=f"Dashboard - {username}", font=("Arial", 16, "bold"))
    title.pack(pady=10)

    logout_button = ctk.CTkButton(master=app, text="Logout", command=logout)
    logout_button.pack(pady=10)

    # GUI elements for requests
    # - Graph all villagers by race, gender, personality, and hobby.
    # - Search all villagers by filtering by race, personality, birthday, and hobby.
    # - Graph showing all catchphrases by beginning letter, amount of words, and amount of letters.
    # - Show the amount of birthdays per month.

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

    request1_dropdown = ctk.CTkOptionMenu(master=request1_frame, values="Species Gender Personality Hobby".split())
    request1_dropdown.pack(side="left", padx=10) 

    request1_button = ctk.CTkButton(master=request1_frame, text="Graph", command=handle_request1)
    request1_button.pack(side="left", padx=10)




    message_input = ctk.CTkEntry(master=app)
    message_input.pack(pady=10, fill="x", padx=10)

    send_button = ctk.CTkButton(master=app, text="Send Message", command=send_message_and_clear)
    send_button.pack(pady=10)

    message_display = ctk.CTkTextbox(master=app, state="normal", height=10)
    message_display.pack(pady=20, fill="both", expand=True)

def handle_data_parameters(data):
    # (['Name', 'Species', 'Gender', 'Personality', 'Hobby', 'Birthday', 'Catchphrase', 'Favorite Song', 'Style 1', 'Style 2', 'Color 1', 'Color 2', 'Wallpaper', 'Flooring', 'Furniture List', 'Filename', 'Unique Entry ID'], {'Species': array(['Bird', 'Squirrel', 'Pig', 'Gorilla', 'Alligator', 'Koala',
    #    'Eagle', 'Anteater', 'Bull', 'Mouse', 'Cat', 'Horse', 'Hamster',
    #    'Kangaroo', 'Wolf', 'Penguin', 'Chicken', 'Elephant', 'Sheep',
    #    'Deer', 'Tiger', 'Cub', 'Dog', 'Bear', 'Hippo', 'Duck', 'Goat',
    #    'Ostrich', 'Rabbit', 'Lion', 'Frog', 'Monkey', 'Rhino', 'Octopus',
    #    'Cow'], dtype=object), 'Personality': array(['Cranky', 'Peppy', 'Big Sister', 'Lazy', 'Normal', 'Snooty',
    #    'Jock', 'Smug'], dtype=object), 'Hobby': array(['Nature', 'Fitness', 'Play', 'Education', 'Fashion', 'Music'],
    #   dtype=object)})
    # above is a print of the data parameters to know the structure of the data
    # 



    logging.info("Handling data parameters")


def handle_request1():
    logging.info(f"handle_request1 called with dropdown value: {request1_dropdown.get()}")
    # get the selected value from the dropdown
    data_type = request1_dropdown.get()
    # send the request to the clienthandler
    # client_handler.send_message({"type": "request_graph", "data_type": data_type})
    client_handler.request_graph(data_type)
    logging.info(f"Graph request sent, type {data_type}")

def update_gui():
    global message_display, username
    while not message_queue.empty():
        try:
            command, data = message_queue.get_nowait()
            if command == "show_dashboard":
                # get the username from the message
                username = data.split()[-1]
                show_dashboard()
            elif command == "login_failed":
                msgbox.showwarning("Login Failed", data if data else "Unknown error")
            elif command == "connection_error":
                show_retry_connection()
            elif command == "connection_success":
                print("Connection to server successful.")
            elif command == "connection_closed":
                print("Connection to server closed.")
            elif command == "show_login":
                show_login()
            elif command == "login_failed":
                logging.error(f"Login failed: {data}")
            # get parameters from the message
            elif command == "data_parameters":
                print("Data parameters received")
                # add a function to handle the data parameters
                handle_data_parameters(data)
                print(data)
            elif command == "graph_data":
                print("Graph data received")
                # add a function to handle the graph data
                print(data)
            # if the command is empty, it is a message from the server
            elif command == "message":
                show_message(f"server: {data}")
            else:
                logging.error(f"Unhandled command: {command}")
        except ValueError as e:
            logging.error(f"Queue message unpacking error: {e}")
        except Exception as e:
            logging.error(f"General error processing GUI update: {e}")
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
