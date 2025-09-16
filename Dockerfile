FROM python:3.12.11-slim-trixie

ENV WORKDIR=/usr/ifms-dev-competition
WORKDIR $WORKDIR

RUN pip install --upgrade pip && pip3 install wheel && pip3 install poetry

COPY ./pyproject.toml $WORKDIR
COPY ./poetry.lock $WORKDIR

RUN poetry install --no-root

COPY ./src $WORKDIR/src

CMD ["poetry", "run", "python3", "-m", "src"]
