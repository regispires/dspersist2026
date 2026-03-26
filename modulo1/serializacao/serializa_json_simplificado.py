import json

# Exemplo de dados - lista de objetos Item
itens = [
	{ "id": 1, "nome": "Produto A", "valor": 29.99, "is_oferta": True },
	{ "id": 2, "nome": "Produto B", "valor": 15.49, "is_oferta": False },
	{ "id": 3, "nome": "Produto C", "valor": 9.99 }
]

with open("itens.json", "w") as f:
	json.dump(itens, f, indent=4)

print("Dados serializados e salvos em 'itens.json'.")