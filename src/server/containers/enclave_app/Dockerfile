FROM enclavebase

WORKDIR /app

COPY server/ ./
COPY requirements.txt ./

# Enclave application code

RUN set -e \
    ### Install required packages
    && pip3 install -r requirements.txt

# Add more packages as required by the application code that will run in the enclave

CMD ["python3", "/app/server.py"]
