FROM python:3.10-slim
WORKDIR /code
COPY ./main/src/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./main/src/main.py /code/
COPY ./unary/posts /code/unary/posts
COPY ./unary/stats /code/unary/stats
EXPOSE 8000