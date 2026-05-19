from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import os
from pathlib import Path
import dotenv
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

from typing import Annotated
from pydantic import BaseModel, ConfigDict

from sqlalchemy.orm import Session
from sqlalchemy.sql import text, update

from database.database import engine, get_db, Base
from datetime import datetime
from database.models import Task, Subtask, User

dotenv.load_dotenv()
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserModel(BaseModel):
    username: str
    password: str
    model_config = ConfigDict(from_attributes=True)

class TokenModel(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class TaskModel(BaseModel):
    title: str
    description: str | None = None
    subtasks: list | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class updateTaskModel(BaseModel):
    title: str | None = None
    description: str | None = None

class SubtaskModel(BaseModel):
    title: str
    model_config = ConfigDict(from_attributes=True)

def get_user(username: str):
    with Session(engine) as session:
        result = session.query(User).filter_by(username=username).first()
        return result 

def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else: 
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError as e:
        raise credentials_exception
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return {"id": user.id, "username": user.username}

# Cria tabelas
Base.metadata.create_all(bind=engine)

@app.post("/register")
async def register(user: UserModel, status_code = status.HTTP_201_CREATED):
    existing_user = get_user(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuário já existe!")
    try:
        with Session(engine) as session:
            hashed_password = password_hash.hash(user.password)
            new_user = User(username=user.username, password=hashed_password)
            session.add(new_user)
            session.commit()
        return {"message": "Usuário registrado com sucesso!"}
    except Exception as e:
        print(e)
        return {"Erro": "Algo deu errado"}

@app.post("/login")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> TokenModel:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return TokenModel(access_token=access_token, token_type="bearer")


@app.get("/users/me")
async def read_users_me(current_user: Annotated[UserModel, Depends(get_current_user)]):
    return current_user

@app.get("/")
async def root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Verificando conexão com banco de dados
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Criar nova tarefa
@app.put("/create-task")
async def create_task(task: TaskModel, current_user: Annotated[UserModel, Depends(get_current_user)], status_code = status.HTTP_201_CREATED):
    try:
        with Session(engine, expire_on_commit=False) as session:
            new_task = Task(title=task.title, description=task.description, user_id=current_user["id"])
            session.add(new_task)
            session.commit()

            #Cria subtarefas relacionadas à tarefa criada
            for subtask in task.subtasks:
                new_subtask = Subtask(task_id=new_task.id, title=subtask)
                session.add(new_subtask)
                session.commit()
            
        return {"message": "Tarefa criada com sucesso!", "ID da tarefa": new_task.id}
    except Exception as e:
        print(e)
        return {"Erro": "Algo deu errado"}
            

# Retornar nova tarefa pelo id
@app.get("/task/{task_id}")
async def get_task(task_id, current_user: Annotated[UserModel, Depends(get_current_user)]):
    result = {}

    with Session(engine) as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")

        subtasks = session.query(Subtask).filter_by(task_id=task_id).all()
        result.update({"task": task})
        result.update({"subtasks": subtasks})

    return {"result": result}


@app.get("/tasks")
async def get_tasks(current_user: Annotated[UserModel, Depends(get_current_user)]):
    with Session(engine) as session:
        tasks = session.query(Task).filter_by(user_id=current_user["id"]).all()
        return {"tasks": tasks}

#Editar uma tarefa
@app.patch("/update-task/{task_id}")
async def update_task(task: updateTaskModel, task_id, current_user: Annotated[UserModel, Depends(get_current_user)]):
    with Session(engine) as session:
        if not session.query(Task).filter_by(id=task_id).first():
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
        task = session.query(Task).filter_by(id=task_id).update({Task.title: task.title, Task.description: task.description})
        session.commit()
    return {"message": "Tarefa atualizada com sucesso!", "ID da tarefa": task_id}

@app.patch("/complete-task/{task_id}")
async def complete_task(task_id, current_user: Annotated[UserModel, Depends(get_current_user)]):
    with Session(engine) as session:
        if not session.query(Task).filter_by(id=task_id).first():
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
        task = session.query(Task).filter_by(id=task_id).update({Task.completed: True})
        session.commit()
    return {"message": "Tarefa marcada como completa!", "ID da tarefa": task_id}

@app.delete("/delete-task/{task_id}")
async def delete_task(task_id):
    return {"message": f"Task {task_id} deleted"}

@app.patch("/update-subtask/{subtask_id}")
async def update_subtask(subtask: SubtaskModel, subtask_id, current_user: Annotated[UserModel, Depends(get_current_user)]):
    with Session(engine) as session:
        if not session.query(Subtask).filter_by(id=subtask_id).first():
            raise HTTPException(status_code=404, detail="Subtarefa não encontrada")
        
        try:
            session.query(Subtask).filter_by(id=subtask_id).update({Subtask.title: subtask.title})
            session.commit()
        except Exception as e:
            print(e)
            return {"Erro": "Não foi possível atualizar a subtarefa", "details": str(e)}  
    return {"message": "Subtarefa atualizada com sucesso!", "ID da subtarefa": subtask_id}

@app.delete("/delete-subtask/{subtask_id}")
async def delete_subtask(subtask_id, current_user: Annotated[UserModel, Depends(get_current_user)]):
    with Session(engine) as session:
        if not session.query(Subtask).filter_by(id=subtask_id).first():
            raise HTTPException(status_code=404, detail="Subtarefa não encontrada")
        try:
            session.query(Subtask).filter_by(id=subtask_id).delete()
            session.commit()
        except Exception as e:
            print(e)
            return {"Erro": "Não foi possível deletar a subtarefa", "details": str(e)}  
    return {"message": "Subtarefa deletada com sucesso!", "ID da subtarefa": subtask_id}