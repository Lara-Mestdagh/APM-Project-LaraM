import socket
import threading
import pickle
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# We use a clienthandler so the client can indirectly communicate with the server

class ClientHandler:
    def __init__(self, host, port, message_queue):
        self.host = host
        self.port = port
        self.message_queue = message_queue      # Queue to send messages to the GUI
        self.client_socket = None               # Socket object for the client
        self.running = False                    

    def send_message(self, data):
        # Send a message to the server
        if self.running and self.client_socket:
            try:
                # Serialize the data
                serialized_data = pickle.dumps(data)
                # Prepend message length before sending
                self.client_socket.sendall(len(serialized_data).to_bytes(4, 'big') + serialized_data)
                logging.info("Message sent to server")
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                self.disconnect("Failed to send message")

    def receive_messages(self):
        while self.running:
            try:
                # Receive the message length
                header = self.client_socket.recv(4)
                if len(header) < 4:
                    raise ConnectionError("Server has closed the connection")
                # Receive the message data
                message_length = int.from_bytes(header, 'big')
                # Receive the message data
                data = b''
                while len(data) < message_length:
                    packet = self.client_socket.recv(message_length - len(data))
                    if not packet:
                        raise ConnectionError("Connection closed by server")
                    data += packet
                # Deserialize the data
                response_data = pickle.loads(data)
                print(f"Clienthandler - Receive Message {response_data}")
                self.handle_response(response_data)
            except ConnectionError as e:
                logging.error(f"Connection error: {e}")
                self.disconnect("Connection lost or server shutdown")
                break
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                continue

    def handle_response(self, response):
        # Handle the response from the server
        if 'type' not in response:
            logging.error("Received a response without a type specifier.")
            return
        
        if response['type'] == 'login_response':
            status = response.get('status', 'failure')
            message = response.get('message', 'No message provided')
            if status == 'success':
                print("Login successful, updating GUI to show dashboard.")
                self.message_queue.put(("show_dashboard", None))
            else:
                print("Login failed, showing error message.")
                self.message_queue.put(("login_failed", message))

    def disconnect(self, reason="Unknown reason"):
        # Clean up connection and inform the user
        if self.running:
            self.running = False
            if self.client_socket:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                    self.client_socket.close()
                except Exception as e:
                    logging.error(f"Error closing socket: {e}")
                finally:
                    self.client_socket = None
                    self.message_queue.put(("connection_closed", f"Connection to server closed. Reason: {reason}"))

    def connect(self):
        # Connect to the server
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.running = True
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.message_queue.put(("connection_success", "Connected to server"))
        except socket.error as e:
            self.running = False
            logging.error(f"Failed to connect to server: {e}")
            self.message_queue.put(("connection_error", "Failed to connect to server."))

    def login(self, username, password):
        print("Clienthandler - Login function called")
        self.send_message({'type': 'login', 'username': username, 'password': password})

    def register(self, name, username, email, password):
        print("Clienthandler - Register function called")
        self.send_message({'type': 'register', 'name': name, 'username': username, 'email': email, 'password': password})