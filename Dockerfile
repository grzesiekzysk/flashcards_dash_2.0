# Użyj oficjalnego obrazu Python
FROM python:3.10-slim

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj pliki aplikacji
COPY . /app

# Zainstaluj zależności
RUN pip install --no-cache-dir -r requirements.txt

# Exponuj port dla aplikacji
EXPOSE 8080

# Uruchom aplikację
CMD ["python", "app.py"]
