import sqlite3
import bcrypt
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

FORMATTER = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

SH = logging.StreamHandler(sys.stdout)
SH.setLevel(logging.INFO)
SH.setFormatter(FORMATTER)

LOGGER.addHandler(SH)

DB_PATH = "app.db"

# Métricas globais
total_requests = 0
login_errors = 0
general_errors = 0

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    usuario = cur.execute(
        "SELECT id FROM usuarios WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not usuario:
        senha_hash = bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO usuarios (username, password) VALUES (?, ?)",
            ("admin", senha_hash)
        )

    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    LOGGER.info("Banco de dados inicializado com sucesso")
    yield

app = FastAPI(title="Formativa Pipeline API", lifespan=lifespan)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/health")
def healthcheck():
    global total_requests
    total_requests += 1
    LOGGER.info("Healthcheck executado com sucesso")
    return {"status": "OK"}

@app.post("/login")
def login(data: LoginRequest):
    global total_requests, login_errors, general_errors
    total_requests += 1

    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT password FROM usuarios WHERE username = ?",
            (data.username,)
        ).fetchone()
        conn.close()

        if row and bcrypt.checkpw(data.password.encode(), row[0].encode()):
            LOGGER.info(f"O usuário {data.username} realizou login com sucesso")
            return {"message": "Login realizado com sucesso"}
        else:
            login_errors += 1
            LOGGER.warning(f"O usuário {data.username} falhou no login")
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

    except HTTPException:
        raise
    except Exception as e:
        general_errors += 1
        LOGGER.error(f"Erro geral na aplicação: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/metricas")
def metrics():
    global total_requests
    total_requests += 1
    LOGGER.info("Consulta de métricas realizada")
    return {
        "quantidade_requisicoes": total_requests,
        "quantidade_erros_login": login_errors,
        "quantidade_erros_gerais": general_errors
    }