# 1. Base on an image that already has Chrome + ChromeDriver
FROM selenium/standalone-chrome:latest

# 2. Install Python 3.10 and pip
USER root
RUN apt-get update && \
    apt-get install -y python3.10 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# 3. Create workdir and copy in your app
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# 4. Expose Streamlit’s default port
EXPOSE 8501

# 5. Launch Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
