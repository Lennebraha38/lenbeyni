FROM python:3.11-slim AS taban
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY voice/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/req.txt

COPY agentv2/ agentv2/
COPY voice/ voice/

EXPOSE 8787
CMD ["python", "-m", "voice.server.run"]