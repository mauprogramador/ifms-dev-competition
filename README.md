# IFMS Dev Competition

<p align="center">
  <img src="./ifms.png" width="150" alt="IFMS">
<p>
<p align="center">
  <em>RESTful API for managing the IFMS Development Competition</em>
</p>
<p align="center">
  <a href="https://github.com/mauprogramador/scopus-survey-api/actions/workflows/verification.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/mauprogramador/scopus-survey-api/verification.yml?branch=master&event=push&logo=github&label=Lint%26Test&color=C5362B" alt="Lint & Test">
  </a>
  <a href="https://github.com/mauprogramador/ifms-dev-competition/releases/latest" target="_blank" rel="external" title="Latest Release">
    <img src="https://img.shields.io/github/v/tag/mauprogramador/ifms-dev-competition?logo=github&label=Release&color=E9711C" alt="Latest Release">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-v3.12-FBDA4E?logo=python&logoColor=FFF&labelColor=3776AB" alt="Python3 version">
  </a>
</p>
<p align="center">
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=FFF" alt="FastAPI">
  </a>
  <a href="https://docs.pydantic.dev/latest/">
    <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=FFF" alt="Pydantic">
  </a>
  <a href="https://opencv.org/">
    <img src="https://img.shields.io/badge/OpenCV-5C3EE8?logo=opencv&logoColor=FFF" alt="OpenCV">
  </a>
  <a href="https://playwright.dev/python/">
    <img src="https://img.shields.io/badge/Playwrigt-6BBB4B?logo=pypi&logoColor=FFF" alt="Playwright">
  </a>
  <a href="https://www.python-httpx.org/">
    <img src="https://img.shields.io/badge/HTTPX-3794F3?logo=pypi&logoColor=FFF" alt="HTTPX">
  </a>
  <a href="https://python-poetry.org/">
    <img src="https://img.shields.io/badge/Poetry-60A5FA?logo=poetry&logoColor=FFF" alt="Poetry">
  </a>
  <a href="https://docs.pytest.org/en/stable/">
    <img src="https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=FFF" alt="Pytest">
  </a>
</p>
<p align="center">
  <a href="https://black.readthedocs.io/en/stable/">
    <img src="https://img.shields.io/badge/code style-black-000" alt="Black">
  </a>
  <a href="https://mypy.readthedocs.io/en/stable/">
    <img src="https://img.shields.io/badge/mypy-checked-2A6DB2" alt="MyPy">
  </a>
  <a href="https://pylint.readthedocs.io/en/stable/">
    <img src="https://img.shields.io/badge/linting-pylint-yellowgreen" alt="Pylint">
  </a>
</p>

---

Federal Institute of Mato Grosso do Sul &nbsp;&#8226;&nbsp; [IFMS - Campus Três Lagoas](https://www.ifms.edu.br/campi/campus-tres-lagoas)
<br/>
Technology in Systems Analysis and Development &nbsp;&#8226;&nbsp; [TADS](https://www.ifms.edu.br/campi/campus-tres-lagoas/cursos/graduacao/analise-e-desenvolvimento-de-sistemas)

- RESTful API: <http://127.0.0.1:8000/v1/ifms-dev-competition/api>
- Swagger UI: <http://127.0.0.1:8000>

---

## Overview

This **RESTful API** was developed to support the exchange of **HTML** and **CSS** files between teams in the **IFMS** programming competition.

### Dynamics

**First:** the pairs of each team will program independently and alternately, with each member in a language (**HTML** or **CSS**) one at a time.

**Last:** the final, one finalist pair per team, the same project for all teams, the order and the way of programming will be decided by the game.

### Teams Count

By default, **30** code directories will be generated for **First** Dynamic, and **10** code directories for **Last** Dynamic.

### Files

Each generated code directory will have two files: a **`HTML`** file type called **index.html** and a **`CSS`** file type called **`style.css`**.

### Rate Limit

This application has a request rate limiting mechanism for **API tagged routes**, accepting up to **60 requests every 2 seconds**. Requests beyond this limit will be responded with an **HTTP 429 error**.

---

## Configuration

You can create an `.env` file to configure the following options:

| **Parameter**   | **Description**                                          | **Default**   |
| --------------- | -------------------------------------------------------- | ------------- |
| `DATABASE_FILE` | Sets the database file (_.db_) absolute path             | `database.db` |
| `HOST`          | Sets the host address to listen on                       | `127.0.0.1`   |
| `PORT`          | Sets the server port on which the application will run   | `8000`        |
| `RELOAD`        | Enable auto-reload on file changes for local development | `false`       |
| `WORKERS`       | Sets multiple worker processes                           | `1`           |
| `LOGGING_FILE`  | Enable saving logs to files                              | `false`       |
| `DEBUG`         | Enable the debug mode and debug logs                     | `false`       |

- The `RELOAD` and `WORKERS` options are **mutually exclusive**.

- Setting the `HOST` to `0.0.0.0` makes the application externally available.

- Set the `DATABASE_FILE` like `/home/user/project/repository/database.db`.

- Set `WORKERS`, **maximum 4**, to start **multiple server processes**.

- Database backup files will be saved inside the `/repository` directory.

> [!TIP]
> Take a look at the [`.env.example`](./.env.example) file.

---

## Run locally with Poetry or Pip

You will need [Python3.12](https://www.python.org/downloads/release/python-31211/) with [Pip](https://pip.pypa.io/en/stable/installation/) and [Venv](https://docs.python.org/3/library/venv.html) installed.

```bash
# Create new Venv
make venv

# Activate Venv
source .venv/bin/activate

# Install dependencies with Poetry [1]
(.venv) make poetry-install

# Install dependencies with Pip [2]
(.venv) make pip-install

# Run the App locally
(.venv) make run
```

## Run with Docker

You will need [Docker](https://www.docker.com/) installed.

```bash
# Run the App in Docker Container
make docker
```

---

For questions or concerns please contact me at <sir.silvabmauricio@gmail.com>.

[License](./LICENSE)
&nbsp;&#8226;&nbsp;
[Latest Release](https://github.com/mauprogramador/ifms-dev-competition/releases/latest)
&nbsp;&#8226;&nbsp;
[Changelog](./CHANGELOG.md)
