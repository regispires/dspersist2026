from fastapi import FastAPI, Body

app = FastAPI()
@app.get("/")
def home():
	return {"msg": "Olá, mundo!"}

@app.get("/posts/{id}")
def get_post(id: int, titulo: str | None = None):
	return {"id": id, "titulo": titulo}

@app.post("/posts/{id}/titulo")
def read_post_str(id: int, titulo: str = Body(default=None)):
	return {"id": id, "titulo": titulo}

@app.post("/posts/{id}")
def read_post_json(id: int, body: dict = Body(default=None)):
	return {"id": id, "titulo": body.get("titulo")}
