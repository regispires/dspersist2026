import sqlite3
from contextlib import contextmanager
@contextmanager
def get_cursor(connection):
	cursor = connection.cursor()
	try:
		yield cursor
	finally:
		cursor.close()

# Exemplo usando o gerenciador de contexto personalizado para cursores
with sqlite3.connect("exemplo.db") as connection:
	with get_cursor(connection) as cursor:
		cursor.execute("SELECT * FROM alunos")
		print(cursor.fetchall())
