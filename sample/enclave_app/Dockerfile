FROM enclavebase

WORKDIR /app

COPY server/ ./
COPY requirements.txt ./

# These commands install prerequisites for the sample application
RUN set -e \
    && pip3 install --upgrade pip \
    && pip3 install -r requirements.txt \
    && export TF_ENABLE_ONEDNN_OPTS=1

CMD ["python3", "/app/server.py"]
