import socket
import threading
import pickle
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ClientHandler:
    def __init__(self, host, port, message_queue):
        # Initialize the client handler with the server host, port, and message queue
        self.host = host
        self.port = port
        self.message_queue = message_queue
        self.client_socket = None
        self.running = False            # Flag to indicate if the client is running
        self.connect_to_server()        # Connect to the server


    def send_message(self, data):
        # don"t send empty messages
        if not data:
            return
        if self.running and self.client_socket:
            try:
                serialized_data = pickle.dumps(data)
                self.client_socket.send(serialized_data)
                logging.info("Message sent to server")
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                self.handle_disconnection("Failed to send message")


    def receive_messages(self):
        buffer_size = 10096  # adjust as needed
        while self.running:
            try:
                response = self.client_socket.recv(buffer_size)
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
        if "type" not in response:
            #if not type is is a message from the server
            self.handle_message(response)
            return
        
        # Long list of possible responses from the server
        # Each response type is handled separately
        if response["type"] == "login_response":                            # Login response
            status = response.get("status", "failure")
            message = response.get("message", "No message provided")
            if status == "success":
                # if login is successful, show the dashboard
                print("Login successful, updating GUI to show dashboard.")
                self.message_queue.put(("show_dashboard", message))
            else:
                # if login is unsuccessful, show an error message
                print("Login failed, showing error message.")
                self.message_queue.put(("login_failed", message))
        elif response["type"] == "register_response":                       # Register response
            status = response.get("status", "failure")
            message = response.get("message", "No message provided")
            if status == "success":
                # if registration is successful, show the login screen
                print("Registration successful, updating GUI to show login.")
                self.message_queue.put(("show_login", None))
            else:
                # if registration is unsuccessful, show an error message
                print("Registration failed, showing error message.")
                self.message_queue.put(("login_failed", message))
        elif response["type"] == "data_parameters":                         # Data parameters response
            print("Received data parameters from server.")
            # need to keep track of the columns
            columns = response.get("columns", [])
            # also need to know the unique values for certain columns
            columns_values = response.get("columns_values", {})
            # combine the columns and values into a single message
            parameters = (columns, columns_values)
            self.message_queue.put(("data_parameters", parameters))
        elif response["type"] == "received_graph1":                         # Graph1 response
            print("Received graph1 data from server.")
            logging.info(f"Graph data received: {response.get('graph_data', 'No data provided')}")
            graph_data = response.get("graph_data", "No data provided")
            # send the graph data to the GUI to be displayed
            self.message_queue.put(("display_graph1", graph_data))
        elif response["type"] == "received_graph2":                         # Graph2 response
            print("Received graph2 data from server.")
            logging.info(f"Graph data received: {response.get('graph_data', 'No data provided')}")
            graph_data = response.get("graph_data", "No data provided")
            # send the graph data to the GUI to be displayed
            self.message_queue.put(("display_graph2", graph_data))
        elif response["type"] == "received_graph3":                         # Graph3 response
            print("Received graph3 data from server.")
            logging.info(f"Graph data received: {response.get('graph_data', 'No data provided')}")
            graph_data = response.get("graph_data", "No data provided")
            data_type = response.get("data_type", "No data type provided")
            # send the graph data to the GUI to be displayed
            self.message_queue.put(("display_graph3", graph_data, data_type))
        elif response["type"] == "search_results":                          # Search villagers response
            print("Received search villagers data from server.")
            search_results = response.get("search_results", "No data provided")
            # send the search results to the GUI to be displayed
            self.message_queue.put(("display_search_results", search_results))
        else:
            # if the response type is not recognized, show an error message
            self.handle_error(response)


    def handle_error(self, response):
        logging.error(f"Unknown response type: {response["type"]} received from server.")
        self.message_queue.put(("error", response["message"]))
        

    def handle_disconnection(self, reason="Unknown reason"):
        if self.running:
            logging.error(f"Disconnection because: {reason}")
            self.close_connection()
            self.message_queue.put(("connection_error", f"Disconnected: {reason}"))


    def handle_message(self, message):
        self.message_queue.put(("message", message))


    def close_connection(self):
        self.running = False            # Set flag to false
        try:
            if self.client_socket:              # Check if the socket is still open, if so close it
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
        except Exception as e:
            logging.error(f"Error closing socket: {e}")
        finally:
            # Reset the client socket to None and notify the client that the connection was closed
            self.client_socket = None
            self.message_queue.put(("connection_closed", "Connection to server closed."))


    def connect_to_server(self):
        try:    
            # Create a socket and connect to the server
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.running = True             # Set flag to true
            # Start a thread to receive messages from the server
            thread = threading.Thread(target=self.receive_messages, daemon=True)
            thread.start()
            # Notify the client that the connection was successful
            self.message_queue.put(("connection_success", "Connected to server"))
            # request the data parameters from the server
            self.request_data()
        except socket.error as e:
            self.running = False
            logging.error(f"Failed to connect to server: {e}")
            self.message_queue.put(("connection_error", "Failed to connect to server."))


    def login(self, username, password):
        self.send_message({"type": "login", "username": username, "password": password})


    def register(self, name, username, email, password):
        self.send_message({"type": "register", "name": name, "username": username, "email": email, "password": password})


    def logout(self):  
        self.send_message({"type": "logout"})


    def request_data(self):
        self.send_message({"type": "request_data_parameters"})


    def request_bar_graph1(self, data_type):
        self.send_message({"type": "request_bar_graph1", "data_type": data_type})


    def request_bar_graph2(self, data_type):
        self.send_message({"type": "request_bar_graph2", "data_type": data_type})


    def request_bar_graph3(self, data_type):
        self.send_message({"type": "request_bar_graph3", "data_type": data_type})


    def request_search_villagers(self, species, personality, hobby):
        parameters = {"species": species, "personality": personality, "hobby": hobby}
        self.send_message({"type": "request_search_villagers", "parameters": parameters})