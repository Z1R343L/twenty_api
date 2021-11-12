FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . /code/
RUN python3 -m pip install --upgrade setuptools wheel > /dev/null 2>&1
RUN python3 -m pip install -r requirements.txt > /dev/null 2>&1
CMD ["uvicorn", "twentyapi.application:app", "--host", "0.0.0.0", "--workers", "4"]
