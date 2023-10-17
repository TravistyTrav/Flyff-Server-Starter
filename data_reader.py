import pickle

DATA_FILE = "server_manager_data.pkl"

def read_data():
    try:
        with open(DATA_FILE, 'rb') as file:
            data = pickle.load(file)
        return data
    except FileNotFoundError:
        return {}  # Return an empty dictionary if the file doesn't exist

# Usage example:
data = read_data()
print(data)