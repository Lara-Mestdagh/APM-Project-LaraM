import customtkinter as ctk
import tkinter.messagebox as msgbox
import queue
import time
import logging
from clienthandler import ClientHandler

class AppGUI:
    def __init__(self, host, port):
        # Initialize the GUI
        self.host = host
        self.port = port
        self.message_queue = queue.Queue()
        # Create a client handler instance and connect to the server
        self.client_handler = ClientHandler(host, port, self.message_queue)
        self.client_handler.connect()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.app = ctk.CTk()
        self.app.title("APM - Animal Crossing Villagers - Client")
        self.app.geometry("600x800")

        # Create the frames
        self.retry_connection_frame = ctk.CTkFrame(master=self.app)
        self.login_frame = ctk.CTkFrame(master=self.app)
        self.dashboard_frame = ctk.CTkFrame(master=self.app)
        self.register_frame = ctk.CTkFrame(master=self.app)
        
        # Create the widgets
        self.setup_frames()
        self.show_login()       # Show the login frame by default if connection is successful
        self.app.after(100, self.update_gui)        # Start the GUI update loop
        self.app.mainloop()     # Start the main event loop

    def setup_frames(self):
        # Set up the frames
        self.setup_retry_connection_frame()
        self.setup_login_frame()
        self.setup_dashboard_frame()
        self.setup_register_frame()

    def setup_retry_connection_frame(self):
        self.retry_connection_frame.pack(fill="both", expand=True)

        title = ctk.CTkLabel(master=self.retry_connection_frame, text="Connection Error")
        title.pack(pady=10)

        message = ctk.CTkLabel(master=self.retry_connection_frame, text="Failed to connect to the server. Trying again...")
        message.pack(pady=10)

        self.progress = ctk.CTkProgressBar(master=self.retry_connection_frame)
        self.progress.pack(pady=20)

        retry_button = ctk.CTkButton(master=self.retry_connection_frame, text="Retry Connection", command=self.attempt_reconnect)
        retry_button.pack(pady=20)

        back_button = ctk.CTkButton(master=self.retry_connection_frame, text="Exit", command=self.app.quit)
        back_button.pack(pady=10)

    def setup_login_frame(self):
        title = ctk.CTkLabel(master=self.login_frame, text="Login")
        title.pack(pady=10)

        self.username_entry = ctk.CTkEntry(master=self.login_frame, placeholder_text="Username")
        self.username_entry.pack(pady=10)
        self.username_entry.focus_set()

        self.password_entry = ctk.CTkEntry(master=self.login_frame, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        login_button = ctk.CTkButton(master=self.login_frame, text="Login", command=self.login)
        login_button.pack(pady=10)

        register_button = ctk.CTkButton(master=self.login_frame, text="Register", command=self.show_register)
        register_button.pack(pady=10)

        self.app.bind('<Return>', self.login)

    def setup_dashboard_frame(self):
        title = ctk.CTkLabel(master=self.dashboard_frame, text="Dashboard", font=("Arial", 15, "bold"))
        title.pack(pady=10)

        logout_button = ctk.CTkButton(master=self.dashboard_frame, text="Logout", command=self.logout)
        logout_button.pack(pady=20)

        self.message_input = ctk.CTkEntry(master=self.dashboard_frame)
        self.message_input.pack(pady=10, fill="x")

        send_button = ctk.CTkButton(master=self.dashboard_frame, text="Send Message", command=self.send_message)
        send_button.pack(pady=10)

        self.message_display = ctk.CTkTextbox(master=self.dashboard_frame, state='disabled', height=10)
        self.message_display.pack(pady=20, fill="both", expand=True)

    def setup_register_frame(self):
        title = ctk.CTkLabel(master=self.register_frame, text="Register")
        title.pack(pady=10)

        name_entry = ctk.CTkEntry(master=self.register_frame, placeholder_text="Name")
        name_entry.pack(pady=10)

        username_entry = ctk.CTkEntry(master=self.register_frame, placeholder_text="Username")
        username_entry.pack(pady=10)

        email_entry = ctk.CTkEntry(master=self.register_frame, placeholder_text="Email")
        email_entry.pack(pady=10)

        password_entry = ctk.CTkEntry(master=self.register_frame, placeholder_text="Password", show="*")
        password_entry.pack(pady=10)

        register_button = ctk.CTkButton(master=self.register_frame, text="Register", command=lambda: self.register(name_entry.get(), username_entry.get(), email_entry.get(), password_entry.get()))
        register_button.pack(pady=10)

        back_button = ctk.CTkButton(master=self.register_frame, text="Back", command=self.show_login)
        back_button.pack(pady=10)

    def show_retry_connection(self):
        self.clear_window()
        self.retry_connection_frame.pack(fill="both", expand=True)

    def show_login(self):
        self.clear_window()
        self.login_frame.pack(fill="both", expand=True)
        # Reset the entry fields to empty
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.username_entry.focus_set()  # Optionally set focus to the username entry


    def show_dashboard(self):
        self.clear_window()
        self.dashboard_frame.pack(fill="both", expand=True)

    def show_register(self):
        self.clear_window()
        self.register_frame.pack(fill="both", expand=True)

    def clear_window(self):
        self.retry_connection_frame.pack_forget()
        self.login_frame.pack_forget()
        self.dashboard_frame.pack_forget()
        self.register_frame.pack_forget()

    def update_gui(self):
        # Process any messages in the message queue
        while not self.message_queue.empty(): 
            # Get the next message from the queue
            command, data = self.message_queue.get_nowait()
            print(f"Command: {command}, Data: {data}")
            if command == "show_dashboard":
                self.show_dashboard()
            elif command == "login_failed":
                msgbox.showwarning("Login Failed", data if data else "Unknown error")
            elif command == "connection_error":
                self.show_retry_connection()
            elif command == "connection_success":
                logging.info("Connection to the server was successful.")
            elif command == "connection_closed":
                msgbox.showwarning("Connection Closed", data if data else "Unknown reason")
                self.show_retry_connection()
            else:
                logging.error(f"Unhandled command: {command}")
        self.app.after(100, self.update_gui)

    def attempt_reconnect(self):
        logging.info("Attempting to reconnect to the server...")
        for i in range(2):  # Try to connect two times
            self.progress.set(i * 50)  # Update progress bar with each attempt
            try:
                self.client_handler.connect()
                if self.client_handler.running:
                    self.progress.set(100)  # Set progress to full on success
                    self.show_login()  # Go to login if connection is successful
                    return
                time.sleep(1)  # Wait for a second before retrying
            except Exception as e:
                logging.error(f"Retry failed: {e}")
                self.progress.set(0)  # Reset progress on failure
        self.show_retry_connection()  # Show the retry screen again if all retries fail

    def login(self, event=None):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.client_handler.login(username, password)

    def send_message(self):
        message = self.message_input.get()
        self.client_handler.send_message(message)

    def logout(self):
        if self.client_handler.running:
            # Send a logout message to the server
            self.client_handler.send_message({'type': 'logout', 'host': self.host})
        self.show_login()

# Create the GUI
app_gui = AppGUI('localhost', 5000)
