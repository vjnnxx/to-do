from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from database.database import engine, get_db, Base
from datetime import datetime
from database import models

app = FastAPI()


class Task(BaseModel):
    title: str
    description: str | None = None
    subtasks: list | None = None
    created_at: datetime | None = None
    update_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Criar nova tarefa
@app.put("/create-task")
async def create_task(task: Task):
    return {"task": task}

# Retornar nova tarefa pelo id
@app.get("/task/{task_id}")
async def get_task(task_id):
    return {"task_id": task_id}

#Editar uma tarefa
@app.patch("/update-task/{task_id}")
async def update_task(task: Task, task_id):
    return {"task": task, "task_id": task_id}

@app.delete("/delete-task/{task_id}")
async def delete_task(task_id):
    return {"message": f"Task {task_id} deleted"}



# Criar / Alterar / Deletar / Listar tarefas