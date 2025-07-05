import os
import json
import markovify
import pickle
from modules.globalvars import *
from modules.translations import _

# Get file size and line count for a given file path
def get_file_info(file_path):
    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, "r") as f:
            lines = f.readlines()
        return {"file_size_bytes": file_size, "line_count": len(lines)}
    except Exception as e:
        return {"error": str(e)}

# Load memory data from file, or use default dataset if not loaded yet
def load_memory():
    data = []

    # Try to load data from MEMORY_FILE
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        pass

    # If MEMORY_LOADED_FILE does not exist, load default data and mark as loaded
    if not os.path.exists(MEMORY_LOADED_FILE):
        try:
            with open(DEFAULT_DATASET_FILE, "r") as f:
                default_data = json.load(f)
                data.extend(default_data) 
        except FileNotFoundError:
            pass
        with open(MEMORY_LOADED_FILE, "w") as f:
            f.write("Data loaded") 
    return data

# Save memory data to MEMORY_FILE
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

# Train a Markov model using memory and optional additional data
def train_markov_model(memory, additional_data=None):
    if not memory:
        return None
    text = "\n".join(memory)
    if additional_data:
        text += "\n" + "\n".join(additional_data)
    model = markovify.NewlineText(text, state_size=2)
    return model

# Save the Markov model to a pickle file
def save_markov_model(model, filename='markov_model.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(model, f)
    print(f"Markov model saved to {filename}.")

# Load the Markov model from a pickle file
def load_markov_model(filename='markov_model.pkl'):
    try:
        with open(filename, 'rb') as f:
            model = pickle.load(f)
        print(f"{GREEN}{_('model_loaded')} {filename}.{RESET}")
        return model
    except FileNotFoundError:
        print(f"{RED}{filename} {_('not_found')}{RESET}")
        return None