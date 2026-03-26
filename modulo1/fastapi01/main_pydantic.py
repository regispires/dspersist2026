from http import HTTPStatus
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
	id: int
	nome: str
	valor: float
	is_oferta: bool | None = None

@app.get("/")
def padrao():
	return {"msg": "Hello World"}

@app.get("/itens/{id}")
def le_id_item(id: int):
	return id

@app.post("/itens/")
def le_item(item: Item):
	return item
