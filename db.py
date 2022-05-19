def get_database():
    from pymongo import MongoClient

    CONNECTION_STRING = "mongodb+srv://dev:magic797BoX@magicboxcluster.l4wqb.mongodb.net/development?retryWrites=true&w=majority"
    client = MongoClient(CONNECTION_STRING)

    return client["development"]
