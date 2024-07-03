from flask_login import UserMixin
from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
client = MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('DB_NAME')]

class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role
    

menus_collection = db['menus']