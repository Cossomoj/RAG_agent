from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Optional

app = FastAPI(title="Admin Panel")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class User(BaseModel):
    id: Optional[int] = None
    username: str
    role: str

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('AI_agent.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return {"message": "Admin Panel API"}

@app.get("/users", response_model=List[User])
async def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return [User(id=user["id"], username=user["username"], role=user["role"]) for user in users]

@app.post("/users", response_model=User)
async def create_user(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, role) VALUES (?, ?)",
        (user.username, user.role)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return User(id=user_id, username=user.username, role=user.role)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088) 