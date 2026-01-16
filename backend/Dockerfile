FROM python:3.10.12-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    APP_HOME=/app \
    PORT=3000

WORKDIR ${APP_HOME}

# RUN apt-get update \
#   && apt-get install -y --no-install-recommends \
#        wget \
#        ffmpeg \
#        curl \
#        libmagic1 \
#        file \
#   && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       wget \
       ffmpeg \
       curl \
       libmagic1 \
       libmagic-mgc \
       file \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt \
  && pip install --no-cache-dir gunicorn

RUN useradd --no-log-init --create-home --shell /bin/false appuser \
  && mkdir -p ${APP_HOME} \
  && chown -R appuser:appuser ${APP_HOME}

COPY --chown=appuser:appuser . ${APP_HOME}

COPY --chmod=0755 ./entrypoint.sh /usr/local/bin/entrypoint.sh

EXPOSE ${PORT}

USER appuser

HEALTHCHECK --interval=180s --timeout=5s --start-period=5s \
  CMD curl -f http://127.0.0.1:${PORT}/health || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "app:app"]