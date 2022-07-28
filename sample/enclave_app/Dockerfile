FROM enclavebase

WORKDIR /app

COPY server/ ./
COPY requirements.txt ./

# These commands install prerequisites for the sample application
RUN set -e \
    && pip3 install -r requirements.txt

CMD ["python3", "/app/server.py"]
