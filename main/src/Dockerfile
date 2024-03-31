FROM python:3.10-slim
WORKDIR /code
COPY ./main/src/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./main/src/main.py /code/
COPY ./unary/unary.proto /code/unary
COPY ./unary/unary_pb2.py /code/unary
COPY ./unary/unary_pb2_grpc.py /code/unary
EXPOSE 8000