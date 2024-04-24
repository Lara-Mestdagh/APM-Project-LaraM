import socket
import logging
import tkinter as tk
from tkinter import messagebox
import threading
from queue import Queue
import customtkinter

class ProjectVillagersClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.running = True
        self.title("Project Villagers Client - Lara Mestdagh")
        self.geometry("800x600")  # Window size
        customtkinter.set_appearance_mode("light")
        customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info('Starting Project Villagers client...')

        self.initWindow()  # Call the initWindow method to initialize the window

        # Connect to server
        self.connect_to_server()

        # Initialize the Queue
        self.message_queue = Queue()

        # Start the listener thread
        self.start_listener()

        # Start processing the queue
        self.after(100, self.process_queue)

    # --------------------------------------------------------------------------------------------
    def initWindow(self):
        # Create GUI components
        self.ping_button = tk.Button(self, text="Ping Server", command=self.ping_server)
        self.ping_button.pack()

        self.message_entry = tk.Entry(self)
        self.message_entry.pack()

        self.send_button = tk.Button(self, text="Send Message", command=self.send_message)
        self.send_button.pack()

        self.response_text = tk.Text(self, height=10, width=50)
        self.response_text.pack()

    # --------------------------------------------------------------------------------------------
    def start_listener(self):
        """Start the listening thread."""
        self.listener_thread = threading.Thread(target=self.listen_to_server, daemon=True)
        self.listener_thread.start()

    # --------------------------------------------------------------------------------------------
    def process_queue(self):
        """Process the queue of messages to be displayed."""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.display_message(message)
        self.after(100, self.process_queue)  # Schedule the next queue processing

    # --------------------------------------------------------------------------------------------
    def send_message(self):
        """Send a message to the server."""
        message = self.message_entry.get()
        if message:
            try:
                logging.info('Sending message to server...')
                self.client_socket.send(message.encode('utf-8'))
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                logging.error(f'Error sending message to server: {e}')
                messagebox.showerror("Error", f"Error sending message to server: {e}")

    # --------------------------------------------------------------------------------------------
    def listen_to_server(self):
        """Listen to the server and put messages into the queue."""
        # log listening to server
        logging.info('Listening to server...')
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                self.message_queue.put(message)
            except ConnectionAbortedError:
                # Handle the disconnection
                self.message_queue.put("Disconnected from server")
                logging.error('Connection was aborted')
                break
            except OSError as e:
                # Handle general OS errors
                self.message_queue.put("OS error occurred")
                logging.error(f'OS error: {e}')
                break
            except Exception as e:
                # Handle other exceptions
                self.message_queue.put("An error occurred")
                logging.error(f'Error receiving message from server: {e}')
                break

    # --------------------------------------------------------------------------------------------
    def display_message(self, message):
        # Safely display the message in the Tkinter text widget
        if self.winfo_exists():  # Check if the Tkinter window still exists
            self.response_text.insert(tk.END, message)
            self.response_text.yview(tk.END)  # Auto-scroll to the end

    # --------------------------------------------------------------------------------------------
    def ping_server(self):
        """Send a ping message to the server."""
        try:
            logging.info('Pinging server...')
            self.client_socket.send('PING\n'.encode('utf-8'))
            # No need to wait for a response here, it will be handled by the listener thread
        except Exception as e:
            logging.error(f'Error pinging server: {e}')
            messagebox.showerror("Error", f"Error pinging server: {e}")

    # --------------------------------------------------------------------------------------------
    def connect_to_server(self):
        try:
            logging.info('Trying to connect to server...')
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', 12345))
            logging.info('Connected to server...')
        except Exception as e:
            logging.error(f'Error connecting to server: {e}')
            messagebox.showerror("Error", f"Error connecting to server: {e}")
            self.destroy()  # Exit the app if the connection fails

    # --------------------------------------------------------------------------------------------
    def on_closing(self):
        try:
            self.client_socket.send('EXIT\n'.encode('utf-8'))
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
        except Exception as e:
            logging.error(f'Error closing client: {e}')
        finally:
            self.destroy()

# --------------------------------------------------------------------------------------------
if __name__ == "__main__":
    app = ProjectVillagersClient()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()