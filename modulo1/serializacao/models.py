
class Item:
	def __init__(self, id: int, nome: str, valor: float, is_oferta: bool | None = None):
		self.id = id
		self.nome = nome
		self.valor = valor
		self.is_oferta = is_oferta

	def __repr__(self):
		return f"Item(id={self.id}, nome='{self.nome}', valor={self.valor}, is_oferta={self.is_oferta})"