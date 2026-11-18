FROM python:3.14-alpine
RUN apk add --no-cache qpdf
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV TZ=Europe/Berlin
EXPOSE 5000
CMD ["python3", "/app/app.py"]
