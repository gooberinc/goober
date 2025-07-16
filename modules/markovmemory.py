import os
import json
import markovify
import pickle
from modules.globalvars import *
from modules.volta.main import _
import logging
logger = logging.getLogger("goober")
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

    return data

# Save memory data to MEMORY_FILE
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

def train_markov_model(memory, additional_data=None):
    if not memory:
        return None
    filtered_memory = [line for line in memory if isinstance(line, str)]
    if additional_data:
        filtered_memory.extend(line for line in additional_data if isinstance(line, str))
    if not filtered_memory:
        return None
    text = "\n".join(filtered_memory)
    model = markovify.NewlineText(text, state_size=2)
    return model

# Save the Markov model to a pickle file
def save_markov_model(model, filename='markov_model.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Markov model saved to {filename}.")

# Load the Markov model from a pickle file
def load_markov_model(filename='markov_model.pkl'):
    try:
        with open(filename, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"{_('model_loaded')} {filename}.{RESET}")
        return model
    except FileNotFoundError:
        logger.error(f"{filename} {_('not_found')}{RESET}")
        return None