# syntax=docker/dockerfile:1

FROM python:3.8-alpine

WORKDIR /app
COPY "requirements.txt" "./"
RUN apk add --no-cache jpeg-dev zlib-dev
RUN apk add --no-cache --virtual .build-deps build-base linux-headers \
    && pip install Pillow
RUN pip install -r requirements.txt
RUN pip install flask[async]

CMD ["flask", "run", "--host=0.0.0.0"]
