# ---- Base Python Image ----
    FROM python:3.11-slim

    # ---- Set Environment Variables ----
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        DISPLAY=:99
    
    # ---- Install Chromium and Dependencies ----
    RUN apt-get update && apt-get install -y \
        chromium \
        chromium-driver \
        wget \
        unzip \
        fonts-liberation \
        libnss3 \
        libxss1 \
        libappindicator3-1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libx11-xcb1 \
        libxcb-dri3-0 \
        libgbm1 \
        libxshmfence1 \
        libxrandr2 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        xdg-utils \
        --no-install-recommends && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*
    
    # ---- Set PATH for Chromium ----
    ENV CHROME_BIN=/usr/bin/chromium
    ENV PATH="${CHROME_BIN}:${PATH}"
    
    # ---- Set Working Directory ----
    WORKDIR /app
    
    # ---- Copy Requirements ----
    COPY requirements.txt .
    
    # ---- Install Python Dependencies ----
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ---- Copy App Code ----
    COPY . .
    
    # ---- Expose Streamlit Port ----
    EXPOSE 8080
      
    # ---- Run the App ----
    CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
    