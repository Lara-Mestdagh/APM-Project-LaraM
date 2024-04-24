import logging
import socket
import tkinter as tk
from tkinter import *
from tkinter import messagebox
import threading
import queue
import customtkinter

class ProjectVillagersClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.running = True
        self.title("Project Villagers Client - Lara Mestdagh")
        self.geometry("800x600")  # Window size
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info('Starting Project Villagers client...')
        self.initWindow()  # Call the initWindow method to initialize the window
        self.makeConnectionWithServer()

        # Create a thread-safe queue for communication between threads
        self.gui_queue = queue.Queue()

        # Start a thread to handle GUI updates from the queue
        threading.Thread(target=self.process_gui_queue, daemon=True).start()

        # Start the main event loop
        self.mainloop()


    # Creation of init_window
    def initWindow(self):
        # Change the title of our widget
        self.title("Login Page")

        customtkinter.set_appearance_mode("light")
        customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

        # Title label
        self.label_title = customtkinter.CTkLabel(self, text="Login", font=("Arial", 24))
        self.label_title.pack(pady=8)  # Add some vertical padding

        # Username label and text entry box
        self.label_username = customtkinter.CTkLabel(self, text="Username:", font=("Arial", 16))
        self.label_username.pack(pady=8)  # Add some vertical padding
        self.entry_username = customtkinter.CTkEntry(self, width=200, placeholder_text="Enter username", font=("Arial", 16))
        self.entry_username.pack()

        # Password label and password entry box
        self.label_password = customtkinter.CTkLabel(self, text="Password:", font=("Arial", 16))
        self.label_password.pack(pady=8)  # Add some vertical padding
        self.entry_password = customtkinter.CTkEntry(self, width=200, placeholder_text="Enter password", show="*", font=("Arial", 16))
        self.entry_password.pack()

        # Login button
        self.button_login = customtkinter.CTkButton(self, text="Login", command=self.loginCallback, font=("Arial", 16))
        self.button_login.pack(pady=16)  # Add some vertical padding

        # Register button
        self.button_register = customtkinter.CTkButton(self, text="Register", command=self.registerCallback, font=("Arial", 16))
        self.button_register.pack()

        # Exit button
        self.button_exit = customtkinter.CTkButton(self, text="Exit App", command=self.exitApp, font=("Arial", 16))
        self.button_exit.pack(pady=16)  # Add some padding and pack the button
    
    def __del__(self):
        logging.info("Closing frame")
        self.closeConnection()

    def exitApp(self):
        self.running = False
        self.closeConnection()
        self.destroy()  # This method closes the tkinter window

    def process_gui_queue(self):
        # This method runs on the main/UI thread and processes messages from the queue
        while self.running:
            try:
                # Get a message from the queue
                message_type, message = self.gui_queue.get(block=True)
                # Process the message (e.g., update the GUI)
                logging.info(f"Processing GUI queue message: {message}")
                if message_type == "Server Response":
                    self.after(0, lambda: messagebox.showinfo("Server Response", message))
                elif message_type == "Error":
                    self.after(0, lambda: messagebox.showinfo("Error", message))
            except queue.Empty:
                # Handle empty queue (no messages to process)
                pass
            except Exception as e:
                # Handle other exceptions
                logging.error(f"Error processing GUI queue: {e}")

    def makeConnectionWithServer(self, attempts=3):
        while attempts > 0:
            try:
                logging.info('Attempting to make connection with server...')
                host = socket.gethostname()
                port = 12345
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((host, port))
                self.in_out_server = self.s.makefile(mode='rw')
                logging.debug('Connection established with server.')  # Change to DEBUG level if INFO is too verbose
                return True
            except Exception as e:
                logging.error('Error making connection with server: %s', e)
                messagebox.showinfo("Error", f"Attempt {4 - attempts} failed: {e}")
                attempts -= 1
                if attempts == 0:
                    messagebox.showinfo("Error", "Failed to connect to server after several attempts.")
                return False

    def closeConnection(self):
        try:
            logging.info('Closing connection with server...')
            self.in_out_server.write("CLOSE\n")
            self.in_out_server.flush()
            self.s.close()
            logging.info('Connection closed with server...')
        except Exception as e:
            logging.error('Error closing connection with server: %s', e)
            messagebox.showinfo("Error", f"Error closing connection with server: {e}")

    def loginCallback(self):
        # Handle login button click
        # Log the event
        logging.info("Login button pressed")
        # Get username and password
        username = self.entry_username.get()
        password = self.entry_password.get()
        if username and password:
            # Start a thread to handle the login
            threading.Thread(target=self.handleLogin, args=(username, password)).start()
        else:
            messagebox.showinfo("Error", "Username and password cannot be empty.")

    def handleLogin(self, username, password):
        try:
            # Send login command to the server
            self.in_out_server.write(f"LOGIN {username} {password}\n")
            self.in_out_server.flush()
            # Wait for response from the server
            response = self.in_out_server.readline().strip()
            # Put the response message in the GUI queue to update the GUI
            self.gui_queue.put(response)
        except Exception as e:
            # Handle exceptions
            logging.error('Error sending login command: %s', e)
            self.gui_queue.put(f"Error sending login command: {e}")

    def registerCallback(self):
        logging.info("Register button pressed")
        username = self.entry_username.get()
        password = self.entry_password.get()
        if username and password:
            threading.Thread(target=self.handleRegister, args=(username, password)).start()
        else:
            messagebox.showinfo("Error", "Username and password cannot be empty.")

    def handleRegister(self, username, password):
        try:
            self.in_out_server.write(f"REGISTER {username} {password}\n")
            self.in_out_server.flush()
            response = self.in_out_server.readline().strip()
            self.gui_queue.put(response)
        except Exception as e:
            logging.error('Error sending register command: %s', e)
            self.gui_queue.put(f"Error sending register command: {e}")

if __name__ == "__main__":
    app = ProjectVillagersClient()
    app.protocol("WM_DELETE_WINDOW", app.exitApp)
    app.mainloop()