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
    for _ in range(3):  # Try to connect three times
        try:
            client_handler.connect_to_server()
            if client_handler.running:
                show_login()  # Or show_dashboard() if you want to go straight to the dashboard after reconnecting
                return
            time.sleep(1)  # Wait for a second before retrying
        except Exception as e:
            logging.error(f"Retry failed: {e}")
    logging.error("Failed to connect to the server. Check your network and try again.")

def logout():
    # if client_handler.running:
    #     client_handler.close_connection()
    show_login()

def show_dashboard():
    clear_window()
    title = ctk.CTkLabel(master=app, text="Dashboard", font=("Arial", 15, "bold"))
    title.pack(pady=10)

    logout_button = ctk.CTkButton(master=app, text="Logout", command=logout)
    logout_button.pack(pady=20)

    message_input = ctk.CTkEntry(master=app)
    message_input.pack(pady=10, fill="x")

    message_display = ctk.CTkTextbox(master=app, state='disabled', height=10)
    message_display.pack(pady=20, fill="both", expand=True)

    send_button = ctk.CTkButton(master=app, text="Send Message", command=lambda: client_handler.send_message(message_input.get()))
    send_button.pack(pady=10)

    print("Dashboard is now displayed.")

def update_gui():
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
                print("Message received from server: ", data)
            else:
                logging.error(f"Unhandled command: {command}")
        except ValueError as e:
            logging.error(f"Queue message unpacking error: {e}")
        except Exception as e:
            logging.error(f"General error processing GUI update: {e}")
    app.after(100, update_gui)


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
