# syntax=docker/dockerfile:1
FROM python:3.13-alpine
WORKDIR /code
RUN apk --no-cache --update-cache add gcc musl-dev gfortran build-base wget freetype-dev libpng-dev openblas-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-u", "main.py"]