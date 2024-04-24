import os
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, Listbox
from queue import Queue
from logging.handlers import QueueHandler, QueueListener
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ServerGUI(tk.Tk):
    def __init__(self, queue):
        # Call the parent class's init method
        super().__init__()

        # Initialize the UI
        self.InitUI()

        # Initialize server variables
        self.active_clients = {}  # Dictionary to track clients
        self.server_running = True

        # Set up logging
        # The GUI queue is used to communicate between the GUI and the server
        self.gui_queue = queue

        # The log queue is used to communicate between the logger and the server
        self.log_queue = Queue()

        # Create an instance of QueueHandler to handle logging messages
        self.queue_handler = QueueHandler(self.log_queue)

        # Set the format for the logging messages
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.queue_handler.setFormatter(formatter)

        # Get the root logger and add the queue handler to it
        logger = logging.getLogger()
        logger.addHandler(self.queue_handler)

        # Set the logging level to INFO
        logger.setLevel(logging.INFO)

        # Create an instance of QueueListener to listen for logging messages
        self.queue_listener = QueueListener(self.log_queue, self.queue_handler)

        # Start the queue listener
        self.queue_listener.start()

        # log end of init
        logging.info('Server GUI initialized')

    def InitUI(self):
        # Set the title of the window
        self.title("Server Dashboard")
        # Set the geometry of the window
        self.geometry("800x600")

        # Create a scrolled text area for displaying messages
        self.text_area = scrolledtext.ScrolledText(self, height=10, width=50)
        self.text_area.pack(padx=10, pady=10)

        # Create an entry field for typing messages
        self.message_entry = tk.Entry(self, width=30)
        self.message_entry.pack(fill=tk.X, padx=10, pady=10)
        
        # Create a send button for sending messages to selected clients
        self.send_button = tk.Button(self, text="Send Message to Selected Clients", command=self.MessageClients)
        self.send_button.pack(pady=10)

        # Create a frame for displaying connected clients
        self.client_list_frame = tk.LabelFrame(self, text="Connected Clients")
        self.client_list_frame.pack(fill=tk.BOTH, expand=True)

        # Create a list box for displaying the list of connected clients
        self.client_list_box = tk.Frame(self.client_list_frame)  # Use a Frame instead of Listbox
        self.client_list_box.pack(padx=10, pady=5)

    def ProcessQueue(self):
        # Continue processing while the queue is not empty
        while not self.gui_queue.empty():
            # Get the next item from the queue
            item = self.gui_queue.get()
            # If the item is a tuple, it's a message with a type and content
            if isinstance(item, tuple):
                type, content = item
                # If the type is "status", it's a status update
                if type == "status":
                    logging.info(content)
                    addr = content.split(' ')[-1]
                    # Handle status updates
                    if "New connection" in content:
                        check_var = tk.BooleanVar(value=False)
                        self.active_clients[addr] = (content, check_var)  # Save socket and BooleanVar
                        self.UpdateClientList()
                    elif "disconnected" in content and addr in self.active_clients:
                            logging.info(f"Removing client {addr} from GUI")
                            del self.active_clients[addr]
                            self.UpdateClientList()
                        # If a client has disconnected
                # If the type is "message", it's a regular message
                elif type == "message":
                    # Display the message in the text area
                    self.text_area.insert(tk.END, f"{content}\n")
                    # Scroll to the end of the text area
                    self.text_area.yview(tk.END)
        # Schedule the next queue processing in 100 ms
        self.after(100, self.ProcessQueue)

    def UpdateClientList(self):
        for widget in self.client_list_box.winfo_children():
            widget.destroy()
        for addr, (_, check_var) in self.active_clients.items():
            cb = tk.Checkbutton(self.client_list_box, text=f"{addr}", variable=check_var)
            cb.pack(anchor='w')

    def MessageClients(self):
        message = self.message_entry.get() + "\n"
        for addr, (client_sock, check_var) in self.active_clients.items():
            if check_var.get():  # Only send to clients with a ticked checkbox
                try:
                    logging.info(f"Sending message to {addr}: {message}")
                    client_sock.send(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Failed to send message to {addr}: {e}")
                    del self.active_clients[addr]
                    self.UpdateClientList()

# This function handles the client connection
def clientHandler(client_socket, addr, gui_queue):
    # Put a status message in the GUI queue
    gui_queue.put(("status", f"New connection from {addr}"))  # Notify GUI of new connection
    with client_socket:
        try:
            while True:
                # Receive data from the client
                data = client_socket.recv(1024).decode('utf-8')
                # If no data is received or the client sends "EXIT", break the loop
                if not data or data == "EXIT":
                    break
                # If the client sends "PING", respond with "PONG"
                if data == "PING\n":
                    response = "PONG\n"
                    client_socket.send(response.encode('utf-8'))
                    # Put a message in the GUI queue
                    gui_queue.put(("message", f"Sent to {addr}: {response}"))  # Log response sent
                # Put the received message in the GUI queue
                gui_queue.put(("message", f"From {addr}: {data}"))  # Push received message to GUI queue
                # Log the received message
                logging.info(f"Received from {addr}: {data}")
        finally:
            # Close the client socket
            client_socket.close()
            # Put a status message in the GUI queue
            gui_queue.put(("status", f"Client {addr} disconnected"))  # Notify GUI of disconnection
            # Log the disconnection
            logging.info(f"Client {addr} has disconnected")

# This function starts the server
def startServer(host, port, gui_queue, server_instance):
    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the host and port
        server_socket.bind((host, port))
        # Start listening for connections
        server_socket.listen()
        # Log the server start
        logging.info(f"Server started on {host}:{port}")

        try:
            # Keep accepting connections while the server is running
            while server_instance.server_running:
                # Accept a connection
                client_sock, addr = server_socket.accept()
                check_var = tk.BooleanVar(value=False)
                server_instance.gui_queue.put(("new_client", (addr, client_sock, check_var)))

                # Start a new thread to handle the client
                threading.Thread(target=clientHandler, args=(client_sock, str(addr), gui_queue), daemon=True).start()
        except KeyboardInterrupt:
            # Log the server stop
            logging.info("Server stopped by user")
        finally:
            # Close the server socket
            server_socket.close()


# This is the entry point of the program
if __name__ == "__main__":
    # Create a queue for the GUI
    gui_queue = Queue()
    # Create a ServerGUI object
    server_gui = ServerGUI(gui_queue)
    
    # Define the host and port
    host = 'localhost'
    port = 12345
    # Start a new thread for the server
    server_thread = threading.Thread(target=startServer, args=(host, port, gui_queue, server_gui), daemon=True)
    server_thread.start()

    # Start the GUI main loop
    server_gui.mainloop()
