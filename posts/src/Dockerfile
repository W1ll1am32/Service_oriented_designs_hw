FROM python:3.10-slim
WORKDIR /code
COPY ./posts/src/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./posts/src/main.py /code/
COPY ./unary/posts /code/unary/posts
EXPOSE 50051
