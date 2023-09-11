def get_database():
    from pymongo import MongoClient

    CONNECTION_STRING = "mongodb+srv://stage:wN3YPq29ZqmZg7RU@reimaginehomeai-2-0.t5kbrrx.mongodb.net/stage?retryWrites=true&w=majority"
    client = MongoClient(CONNECTION_STRING)

    return client["stage"]
