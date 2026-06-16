import asyncio
from pymongo import AsyncMongoClient

async def main():
	uri = "mongodb://localhost:27017"
	client = AsyncMongoClient(uri)

	db = client.mydatabase
	collection = db.mycollection

	await collection.insert_one({"name": "José", "status": "Connected!"})
	result = await collection.find_one({"name": "José"})
	print(result)

	await client.close()

asyncio.run(main())
