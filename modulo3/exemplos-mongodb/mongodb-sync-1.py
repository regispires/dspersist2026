from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.mydatabase
collection = db.mycollection

# Inserir um documento
collection.insert_one({"name": "João", "age": 30})

# Buscar um documento
result = collection.find_one({"name": "João"})
print(result)
