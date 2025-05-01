FROM python:3.9-slim

# Install LibreOffice
RUN apt-get update && apt-get install -y libreoffice

WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Use gunicorn as production server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
