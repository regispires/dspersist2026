import asyncio
from pymongo import AsyncMongoClient

client = AsyncMongoClient("mongodb://localhost:27017/")

db = client.mydatabase
collection = db.mycollection

async def main():
	doc = await collection.find_one({"name": "João"})
	print(doc)
	await client.close()

asyncio.run(main())
