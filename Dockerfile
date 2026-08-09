# Temel imaj olarak hafif bir Python 3.9 veya üstü sürümü kullanıyoruz
FROM python:3.9-slim

# Çalışma dizinini belirliyoruz
WORKDIR /app

# Proje kodlarını çalışma dizinine kopyalıyoruz
COPY . /app/

# Uygulama hiçbir dış paket gerektirmiyor (Saf Python Standard Library)
# Eğer ileride gereksinim eklerseniz aşağıdaki satırı kullanabilirsiniz:
# RUN pip install --no-cache-dir -r requirements.txt

# Cloud platformlarının atayacağı PORT çevre değişkenini kullanmak üzere sunucuyu başlatıyoruz
# Varsayılan port 8080'dir.
EXPOSE 8080

# Sunucuyu çalıştıran komut
CMD ["python", "api_server.py"]
