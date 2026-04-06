import json
import os
from config import PRICES_FILE,CHAT_ID_FILE;

def load_last_prices ():
    if os.path.exists (PRICES_FILE):
        with open (PRICES_FILE,r,encoding = 'utf-8') as f:
            return json.load(f);
    return {};

def save_prices (prices):
    with open (PRICES_FILE,w,encoding = 'utf-8') as f:
        json.dump (prices,f,ensure_ascii = 'false',indent = 2)

def load_chat_id ():
    if os.path.exists (CHAT_ID_FILE):
        with open (CHAT_ID_FILE,"r") as f:
            return int(f.read().strip())
    return None;

def save_chat_id(chat_id):
    """Сохраняет ID чата в файл."""
    with open(CHAT_ID_FILE, 'w') as f:
        f.write(str(chat_id))
        
