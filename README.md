# IFMS Dev Competition

<p align="center">
  <em>RESTful API for managing the IFMS Development Competition</em>
</p>
<p align="center">
  <a href="https://github.com/mauprogramador/ifms-dev-competition/releases/latest" target="_blank" rel="external" title="Latest Release">
    <img src="https://img.shields.io/github/v/tag/mauprogramador/ifms-dev-competition?logo=github&label=Release&color=E9711C" alt="Latest Release">
  </a>
  <a href="https://www.python.org/" target="_blank" rel="external" title="Python3 Version">
    <img src="https://img.shields.io/badge/Python-v3.11-FBDA4E?logo=python&logoColor=FFF&labelColor=3776AB" alt="Python3 Version">
  </a>
  <a href="https://fastapi.tiangolo.com/" target="_blank" rel="external" title="FastAPI">
    <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=FFF" alt="FastAPI">
  </a>
  <a href="https://docs.pydantic.dev/latest/" target="_blank" rel="external" title="Pydantic">
    <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=FFF" alt="Pydantic">
  </a>
  <a href="https://black.readthedocs.io/en/stable/" target="_blank" rel="external" title="Black">
    <img src="https://img.shields.io/badge/Black-000?logo=readthedocs&logoColor=FFF" alt="Black">
  </a>
</p>

---

Federal Institute of Mato Grosso do Sul - <a href="https://www.ifms.edu.br/campi/campus-tres-lagoas" target="_blank" rel="external" title="IFMS - Campus Três Lagoas">IFMS - Campus Três Lagoas</a><br/>
Technology in Systems Analysis and Development - <a href="https://www.ifms.edu.br/campi/campus-tres-lagoas/cursos/graduacao/analise-e-desenvolvimento-de-sistemas" target="_blank" rel="external" title="TADS">TADS</a><br/>

**RESTful API**: <a href="http://127.0.0.1:8000/v1/ifms-dev-competition/api" target="_blank" rel="external" title="Web API">http://127.0.0.1:8000/v1/ifms-dev-competition/api</a>

**Swagger UI**: <a href="http://127.0.0.1:8000/docs" target="_blank" rel="external" title="Swagger UI">http://127.0.0.1:8000/docs</a>

---

## Overview

This **RESTful API** was developed to support the exchange of **HTML** and **CSS** files between teams in the **IFMS** programming competition.

**1st Dynamic:** the pairs of each team will program independently and alternately, with each member in a language (**HTML** or **CSS**) one at a time.

**2nd Dynamic:** the final, one finalist pair per team, the same project for all teams, the order and the way of programming will be decided by the game.

---

## Configuration

You can create an `.env` file to configure the following options:

| **Parameter**  | **Description**                                          | **Default** |
| -------------- | -------------------------------------------------------- | ----------- |
| `host`         | Sets the host address to listen on                       | `127.0.0.1` |
| `port`         | Sets the server port on which the application will run   | `8000`      |
| `reload`       | Enable auto-reload on file changes for local development | `false`     |
| `workers`      | Sets multiple worker processes                           | `1`         |
| `logging_file` | Enable saving logs to files                              | `false`     |
| `debug`        | Enable the debug mode and debug logs                     | `false`     |

- The `reload` and `workers` options are **mutually exclusive**.

- Setting the `host` to `0.0.0.0` makes the application externally available.

Take a look at the [`.env.example`](./.env.example) file.

---

## Run locally

You will need <a href="https://www.python.org/downloads/release/python-3117/" target="_blank" rel="external" title="Python3.11">Python3 `v3.11`</a> with <a href="https://pip.pypa.io/en/stable/installation/" target="_blank" rel="external" title="Pip">Pip</a> and <a href="https://docs.python.org/3/library/venv.html" target="_blank" rel="external" title="Pip">Venv</a> installed.

```bash
# Create new Venv
python3.11 -m venv .venv

# Activate Venv
source .venv/bin/activate

# Install dependencies with Poetry
(.venv) make install

# Install dependencies with Pip
(.venv) pip3 install -r requirements.txt

# Run the API locally
(.venv) make run
```

## Run in Docker

You will need <a href="https://www.docker.com/" target="_blank" rel="external" title="Docker">Docker</a> installed.

```bash
# Run the App in Docker Container
make docker
```

---

This project is licensed under the terms of the [MIT license](./LICENSE)
