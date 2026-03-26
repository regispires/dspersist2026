from pydantic import BaseModel

class Item(BaseModel):
	id: int | None = None
	nome: str
	valor: float
	is_oferta: bool | None = None
