import customtkinter as ctk
import tkinter.messagebox as msgbox
import queue
import time
import logging
from clienthandler import ClientHandler

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = 'localhost'
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
        message_input.delete(0, 'end')  # Clear the input field after sending the message

def show_dashboard():
    global message_display, message_input
    clear_window()
    title = ctk.CTkLabel(master=app, text="Dashboard", font=("Arial", 15, "bold"))
    title.pack(pady=10)

    logout_button = ctk.CTkButton(master=app, text="Logout", command=logout)
    logout_button.pack(pady=20)

    message_display = ctk.CTkTextbox(master=app, state='normal', height=10)
    message_display.pack(pady=20, fill="both", expand=True)

    message_input = ctk.CTkEntry(master=app)
    message_input.pack(pady=10, fill="x")

    send_button = ctk.CTkButton(master=app, text="Send Message", command=send_message_and_clear)
    send_button.pack(pady=10)

def update_gui():
    global message_display
    while not message_queue.empty():
        try:
            command, data = message_queue.get_nowait()
            if command == "show_dashboard":
                show_dashboard()
            elif command == "login_failed":
                msgbox.showwarning("Login Failed", data if data else "Unknown error")
            elif command == "connection_error":
                show_retry_connection()
            elif command == "connection_success":
                print("Connection to server successful.")
            elif command == "connection_closed":
                print("Connection to server closed.")
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
    message_display.insert('end', message + '\n')
    message_display.see('end')

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
    app.bind('<Return>', on_enter_key)  # Bind the Enter key to the login action

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
