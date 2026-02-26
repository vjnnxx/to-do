from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import os
import dotenv
import jwt
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

from typing import Annotated
from pydantic import BaseModel, ConfigDict

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

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

class TaskModel(BaseModel):
    title: str
    description: str | None = None
    subtasks: list | None = None
    created_at: datetime | None = None
    update_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

# def fake_decode_token(token):
#     return UserModel(
#         username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
#     )
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
    user = fake_decode_token(token)
    return user

# Cria tabelas
Base.metadata.create_all(bind=engine)

@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> TokenModel:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return TokenModel(access_token=access_token, token_type="bearer")
    ### Criar usuário


@app.get("/users/me")
async def read_users_me(current_user: Annotated[UserModel, Depends(get_current_user)]):
    return current_user

@app.get("/")
async def root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # VEricando conexão com banco de dados
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
async def get_task(task_id):
    return {"task_id": task_id}

#Editar uma tarefa
@app.patch("/update-task/{task_id}")
async def update_task(task: TaskModel, task_id):
    return {"task": task, "task_id": task_id}

@app.delete("/delete-task/{task_id}")
async def delete_task(task_id):
    return {"message": f"Task {task_id} deleted"}