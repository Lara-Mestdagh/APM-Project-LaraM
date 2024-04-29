import socket
import threading
import pickle
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ClientHandler:
    def __init__(self, host, port, message_queue):
        self.host = host
        self.port = port
        self.message_queue = message_queue
        self.client_socket = None
        self.running = False
        self.connect_to_server()

    def send_message(self, data):
        if self.running and self.client_socket:
            try:
                serialized_data = pickle.dumps(data)
                self.client_socket.send(serialized_data)
                logging.info("Message sent to server")
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                self.handle_disconnection("Failed to send message")

    def receive_messages(self):
        while self.running:
            try:
                response = self.client_socket.recv(1024)
                if not response:
                    raise ConnectionResetError("Server has closed the connection")
                response_data = pickle.loads(response)
                self.handle_response(response_data)
            except (pickle.UnpicklingError, IndexError) as e:
                logging.error(f"Data corruption or incomplete data received: {e}")
                continue
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                self.handle_disconnection(str(e))
                break

    def handle_response(self, response):
        if 'type' not in response:
            logging.error("Received a response without a type specifier.")
            return
        
        print("Handle_response - clienthandler.py")
        print(response)

        if response['type'] == 'login_response':
            status = response.get('status', 'failure')
            message = response.get('message', 'No message provided')
            if status == 'success':
                print("Login successful, updating GUI to show dashboard.")
                self.message_queue.put(("show_dashboard", None))  # Ensure second value is None if no additional data
            else:
                print("Login failed, showing error message.")
                self.message_queue.put(("login_failed", message))


    def handle_error(self, response):
        logging.error(f"Error from server: {response['message']}")
        self.message_queue.put(("error", response['message']))
        
    def handle_disconnection(self, reason="Unknown reason"):
        if self.running:
            logging.error(f"Disconnection because: {reason}")
            self.close_connection()
            self.message_queue.put(("connection_error", f"Disconnected: {reason}"))

    def close_connection(self):
        self.running = False
        try:
            if self.client_socket:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
        except Exception as e:
            logging.error(f"Error closing socket: {e}")
        finally:
            self.client_socket = None
            self.message_queue.put(("connection_closed", "Connection to server closed."))

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.running = True
            thread = threading.Thread(target=self.receive_messages, daemon=True)
            thread.start()
            self.message_queue.put(("connection_success", "Connected to server"))
        except socket.error as e:
            self.running = False
            logging.error(f"Failed to connect to server: {e}")
            self.message_queue.put(("connection_error", "Failed to connect to server."))

    def login(self, username, password):
        self.send_message({'type': 'login', 'username': username, 'password': password})

    def register(self, name, username, email, password):
        self.send_message({'type': 'register', 'name': name, 'username': username, 'email': email, 'password': password})