FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . /code/
RUN pip3 install -r requirements.txt
CMD ["uvicorn", "twentyapi.application:app", "--host", "0.0.0.0"]
