import pickle
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ClientHandler(threading.Thread):
    def __init__(self, client_socket, client_address, message_queue, message_recieved_callback=None):
        self.client_socket = client_socket
        self.client_address = client_address
        self.message_queue = message_queue,
        self.message_recieved_callback = message_recieved_callback,
        self.running = True

    def run(self) -> None:
        # start the client handler
        self.accept_connections()

    def accept_connections(self):
        while self.running:
            try:
                # Receive data from the client
                data = self.client_socket.recv(1024)
                if data:
                    # Process the data
                    self.process_data(data)
                    self.message_recieved_callback(data)
                else:
                    # If no data is received, the client has disconnected
                    self.running = False
            except Exception as e:
                logging.error(f"Error receiving data from client {self.client_address}: {e}")
                self.running = False

    # Process the data received from the client
    def process_data(self, data):
        # Unpickle the data, if it fails, return an error
        try:
            request = pickle.loads(data)    
            # check if the request is in proper format type and data
            if 'type' not in request or 'data' not in request:
                logging.error(f"Invalid request from client {self.client_address}")
                return
            else:
                # send the request to the message queue
                print("Request sent from handler to server")
                self.message_queue.put(request)
        except Exception as e:
            logging.error(f"Error unpickling data from client {self.client_address}: {e}")
            return
        
    # Send a response back to the client
    def send_response(self, response):
        try:
            # Pickle the response
            response_data = pickle.dumps(response)
            # Send the response to the client
            self.client_socket.send(response_data)
        except Exception as e:
            logging.error(f"Error sending response to client {self.client_address}: {e}")
        






    def handle_client(client_socket):
        global message_queue
        while True:
            try:
                message = message_queue.get()
                if not message:
                    # if no message is received, the client has disconnected
                    remove_client(client_socket)
                    break


                # Process the message here
                # Unpickle the message

                # Check the type of message
                if message["type"] == "user_login":
                    handle_login(message["data"], client_socket)
                elif message["type"] == "user_register":
                    handle_register(message["data"], client_socket)
                elif message["type"] == "user_logout":
                    print("User logout request received")
                    remove_client(client_socket)
                elif message["type"] == "request_bar_graph1":
                    handle_request_bar_graph1(message["data"], client_socket)
                elif message["type"] == "request_bar_graph2":
                    handle_request_bar_graph2(message["data"], client_socket)
                elif message["type"] == "request_bar_graph3":
                    handle_request_bar_graph3(message["data"], client_socket)
                elif message["type"] == "request_search_villagers":
                    handle_request_search_villagers(message["data"], client_socket)
                elif message["type"] == "request_data_parameters":
                    print("Data parameters request received")

            except ConnectionResetError:
                logging.error("ConnectionResetError: Client disconnected unexpectedly")
                remove_client(client_socket)
                break

    def read_dataset():
    global dataset
    # Load the dataset from the file 
    try:
        dataset = pd.read_csv("./data/Animal_Crossing_Villagers.csv", dtype={
            'Name': 'str', 'Species': 'str', 'Gender': 'str', 'Personality': 'str', 'Hobby': 'str'
        })
        logging.info("Dataset loaded successfully")

        # TODO: Add any additional processing here
        # Drop rows with missing values
        dataset = dataset.dropna()
        logging.info(f"Rows with missing values dropped, remaining rows: {len(dataset)}")

        # Convert Birthday to datetime
        dataset['Birthday'] = pd.to_datetime(dataset['Birthday'], format='%d-%b')

        # Drop unnecessary columns
        drop_cols = ['Favorite Song', 'Style 1', 'Style 2', 'Color 1', 'Color 2', 'Wallpaper', 'Flooring', 'Furniture List', 'Filename']
        dataset = dataset.drop(columns=drop_cols)
        logging.info("Unnecessary columns dropped.")

        return dataset
    except Exception as e:
        logging.error(f"Error loading dataset: {e}")
        return None
    



    def handle_request_bar_graph1(data_type, client_socket):
    # graph data is column name, get the unique values and their counts to send to the client
    global dataset
    if dataset is None:
        response = {"type": "graph", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Graph request denied: Dataset not loaded")
    else:
        try:
            # get the unique values and their counts
            graph_data = dataset[data_type].value_counts()
            response = {"type": "received_graph1", "status": "success", "graph_data": graph_data}
        except Exception as e:
            response = {"type": "received_graph1", "status": "failure", "message": f"Error processing graph data: {e}"}
            logging.error(f"Error processing graph data: {e}")

    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")

def handle_request_bar_graph2(data_type, client_socket):
    global dataset  
    if dataset is None:
        response = {"type": "graph", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Graph request denied: Dataset not loaded")
    else:
        try:
             # Extract the month from the date column
            dataset['Month'] = pd.to_datetime(dataset[data_type]).dt.month
            # Count the number of occurrences of each month
            graph_data = dataset['Month'].value_counts().sort_index()            
            response = {"type": "received_graph2", "status": "success", "graph_data": graph_data}
        except Exception as e:
            response = {"type": "received_graph2", "status": "failure", "message": f"Error processing graph data: {e}"}
            logging.error(f"Error processing graph data: {e}")
    
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")
        
def handle_request_bar_graph3(data_type, client_socket):
    # depending on data_type graph catchphrases by beginning letter, amount of words, and amount of letters.
    global dataset
    if dataset is None:
        response = {"type": "graph", "status": "failure", "message": "Dataset not loaded"}
        logging.warning("Graph request denied: Dataset not loaded")
    else:
        try:
            if data_type == "Starting letter":
                # Catchphrases by beginning letter
                catchphrase_dataset = dataset["Catchphrase"].str[0].str.upper()
                catchphrase_letter = catchphrase_dataset.value_counts().sort_index()
                graph_data = catchphrase_letter
            elif data_type == "Word count":
                # Catchphrases by amount of words
                catchphrase_dataset = dataset["Catchphrase"].str.split().str.len()
                catchphrase_words = catchphrase_dataset.value_counts().sort_index()
                graph_data = catchphrase_words
            elif data_type == "Letter count":
                # Catchphrases by amount of letters
                catchphrase_dataset = dataset["Catchphrase"].str.len()
                catchphrase_letters = catchphrase_dataset.value_counts().sort_index()
                graph_data = catchphrase_letters

            response = {"type": "received_graph3", "status": "success", "graph_data": graph_data, "data_type": data_type}
        except Exception as e:
            response = {"type": "received_graph3", "status": "failure", "message": f"Error processing graph data: {e}"}
            logging.error(f"Error processing graph data: {e}")
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]["username"]}: {e}")


def handle_request_search_villagers(parameters, client_socket):
    logging.info(f"Searching villagers with parameters: {parameters}")
    global dataset
    if dataset is None:
        data = {"status": "failure", "message": "Dataset not loaded"}
        logging.warning("Data parameters request denied: Dataset not loaded")
    else:
        columns = dataset.columns.tolist()
        species_values = dataset['Species'].unique()
        personality_values = dataset['Personality'].unique()
        hobby_values = dataset['Hobby'].unique()

        columns_values = {
            "Species": species_values,
            "Personality": personality_values,
            "Hobby": hobby_values
        }

        data = {"status": "success", "columns": columns, "columns_values": columns_values}
        logging.info("Data parameters sent successfully")

    response = {"type": "data_parameters", "data": data}

    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]['username']}: {e}")
        remove_client(client_socket)

def handle_request_data_parameters(client_socket):
    global dataset
    if dataset is None:
        data = {"status": "failure", "message": "Dataset not loaded"}
        response = {"type": "data_parameters", "data": data}
        logging.warning("Data parameters request denied: Dataset not loaded")
    else:
        # get the columns and the unique values for species, personality, and hobby
        columns = dataset.columns.tolist()
        species_values = dataset['Species'].unique()
        personality_values = dataset['Personality'].unique()
        hobby_values = dataset['Hobby'].unique()
        # group the values into a dictionary
        columns_values = {
            "Species": species_values,
            "Personality": personality_values,
            "Hobby": hobby_values
        }
        data = {
            "columns": columns,
            "columns_values": columns_values
        }
        response = {"type": "data_parameters", "data": data}
        logging.info("Data parameters sent successfully")
    try:
        client_socket.send(pickle.dumps(response))
    except Exception as e:
        logging.error(f"Error sending response to {clients[client_socket]['username']}: {e}")
        remove_client(client_socket)