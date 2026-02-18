
FROM python:3.14-slim


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./app /code/app

COPY ./database /code/database


CMD ["fastapi", "run", "app/main.py", "--port", "80"]