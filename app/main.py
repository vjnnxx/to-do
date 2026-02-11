from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    title: str
    description: str | None = None
    subtasks: list | None = None


@app.get("/")
async def root():
    return {"message": "Hello, World!"}

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