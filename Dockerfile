FROM tiangolo/uvicorn-gunicorn-fastapi:latest
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . /code/
RUN pip install -q -r requirements.txt > /dev/null 2>&1
CMD ["uvicorn", "fastapiredis.application:app", "--host", "0.0.0.0"]
