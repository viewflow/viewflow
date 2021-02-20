/* eslint-env node */
const render = (ctx) => `[tool.poetry]
name = "${ctx.project}"
version = "0.1.0"
description = ""
authors = []

[tool.poetry.dependencies]
python = ">=3.6"
django = ">=3.1b1"
${ctx.rest ? `djangorestframework = ">3.10"
`:''}${ctx.deploy ? `django-environ = ""
`:''}${ctx.deploy ? `psycopg2-binary = {version = "", optional = true}
`:''}${ctx.deploy ? `gunicorn = {version = "", optional = true}
`:''}${ctx.deploy & ctx.asgi ? `uvicorn = {version = "", optional = true}
`:''}${ctx.deploy & ctx.asgi ? `uvloop = {version = "", optional = true}
`:''}${ctx.deploy & ctx.asgi ? `httptools = {version = "", optional = true}
`:''}${ctx.celery ? `celery = ">4"
`:''}${ctx.celery || ctx.redis ? `redis = ">3.2.0"
`:''}${ctx.redis ? `django-redis = ">4.10"
`:''}

[tool.poetry.dev-dependencies]
${ctx.deploy ? `ansible = ">=2.10.0a7" # https://github.com/python-poetry/poetry/issues/2251
`: ''}${ctx.deploy ? `jinja2 = ""
`: ''}${ctx.deploy ? `PyYAML = ""
`: ''}${ctx.deploy ? `cryptography = ""
`: ''}${ctx.deploy ? `packaging = ""`: ''}

${ctx.deploy ? `[tool.poetry.extras]
production = ["gunicorn", ${ctx.asgi ? '"uvicorn", "uvloop", "httptools", ':''}"psycopg2-binary"]`:''}

[build-system]
requires = ["poetry>=0.12"]
build-backend = "poetry.masonry.api"
`;

exports.default = render;
