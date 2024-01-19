FROM python:3.8
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir Flask==2.2.5 Flask-SQLAlchemy==3.1.1 Flask-CORS==3.0.10 mysql-connector-python psycopg2-binary==2.9.9
EXPOSE 8080
ENV NAME World
CMD ["python", "app.py"]