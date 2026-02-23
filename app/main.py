from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from database.database import engine, get_db, Base
from datetime import datetime
from database.models import Task
import json

app = FastAPI()


class TaskModel(BaseModel):
    title: str
    description: str | None = None
    subtasks: dict | None = None
    created_at: datetime | None = None
    update_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello, World! ITS ALIVE!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Criar nova tarefa
@app.put("/create-task")
async def create_task(task: TaskModel, status_code = status.HTTP_201_CREATED):
    try:
        with Session(engine) as session:
            new_task = Task(title=task.title, description=task.description,)
            session.add(new_task)
            session.commit()
        return {"message": "Tarefa criada com sucesso!"}
    except Exception as e:
        print(e)
        return {"Erro": "Algo deu errado"}
            

# Retornar nova tarefa pelo id
@app.get("/task/{task_id}")
async def get_task(task_id):
    return {"task_id": task_id}

#Editar uma tarefa
@app.patch("/update-task/{task_id}")
async def update_task(task: TaskModel, task_id):
    return {"task": task, "task_id": task_id}

@app.delete("/delete-task/{task_id}")
async def delete_task(task_id):
    return {"message": f"Task {task_id} deleted"}