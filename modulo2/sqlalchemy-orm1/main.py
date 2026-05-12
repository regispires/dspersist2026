from sqlalchemy.orm import Session
from models import Aluno
from database import engine

with Session(engine) as session:
	try:
		session.add(Aluno(nome='Maria', apelido='Mari'))
		session.add(Aluno(nome='João', email='joao@example.com'))
		session.commit()
	except Exception as e:
		session.rollback()
		print(f'Erro: {e}')

	alunos = session.query(Aluno).all()
	for aluno in alunos:
		print(aluno)
