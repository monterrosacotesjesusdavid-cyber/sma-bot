FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip xvfb \
    libxi6 libnss3 libxss1 \
    libatk-bridge2.0-0 libgtk-3-0 \
    libgbm-dev libasound2t64 \
    fonts-liberation xdg-utils \
    ca-certificates \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Chrome + ChromeDriver versión exacta matching
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.91/linux64/chrome-linux64.zip" -O /tmp/chrome.zip \
    && unzip /tmp/chrome.zip -d /opt/ \
    && ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome-stable \
    && rm /tmp/chrome.zip

RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.91/linux64/chromedriver-linux64.zip" -O /tmp/cd.zip \
    && unzip /tmp/cd.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/cd.zip

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
