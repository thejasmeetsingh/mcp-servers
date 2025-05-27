FROM python:3.11-alpine

RUN apk add --no-cache build-base libffi-dev
RUN pip install --upgrade pip

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "mcp", "run", "main.py" ]
