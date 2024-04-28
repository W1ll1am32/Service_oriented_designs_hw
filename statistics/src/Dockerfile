FROM python:3.10-slim
WORKDIR /code
COPY ./statistics/src/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./statistics/src/main.py /code/
EXPOSE 8001
