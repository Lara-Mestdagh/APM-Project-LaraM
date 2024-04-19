import socket
import logging
import tkinter as tk
from tkinter import messagebox

class ProjectVillagersClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Villagers Client - Lara Mestdagh")
        # Set up logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info('Starting Project Villagers client...')

        # Connect to server
        self.connect_to_server()

        # Create GUI components
        self.ping_button = tk.Button(self, text="Ping Server", command=self.ping_server)
        self.ping_button.pack()

        self.message_entry = tk.Entry(self)
        self.message_entry.pack()

        self.send_button = tk.Button(self, text="Send Message", command=self.send_message)
        self.send_button.pack()

        self.response_text = tk.Text(self, height=10, width=50)
        self.response_text.pack()

    def send_message(self):
        message = self.message_entry.get()
        if message:
            try:
                logging.info('Sending message to server...')
                self.client_socket.send(message.encode('utf-8'))
                response = self.client_socket.recv(1024).decode('utf-8')
                logging.info(f'Server response: {response}')
                self.response_text.insert(tk.END, f'Server: {response}\n')
            except Exception as e:
                logging.error(f'Error sending message to server: {e}')
                messagebox.showerror("Error", f"Error sending message to server: {e}")

    def ping_server(self):
        try:
            logging.info('Pinging server...')
            self.client_socket.send('PING'.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            logging.info(f'Server response: {response}')
            messagebox.showinfo("Server response", f"Server response: {response}")
        except Exception as e:
            logging.error(f'Error pinging server: {e}')
            messagebox.showerror("Error", f"Error pinging server: {e}")

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

    def on_closing(self):
        try:
            self.client_socket.send('EXIT'.encode('utf-8'))
            self.client_socket.close()
        except Exception as e:
            logging.error(f'Error closing client: {e}')
        finally:
            self.destroy()

if __name__ == "__main__":
    app = ProjectVillagersClient()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
