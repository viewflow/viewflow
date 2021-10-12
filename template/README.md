# npm init django

`./django-admin startproject` in a virtualenv with the single command.

![Demo run gif](https://github.com/viewflow/viewflow/raw/v2/assets/ProjectTempate.gif "Demo")


## Introduction

Unlike other cookiecutter templates which create thousands of files even in the default case, this project aims to provide a bare-minimum project template, with only the required code

The command started without any options, produce the same output as Django `startproject` command

To use full-power of this package [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) and [poetry](https://python-poetry.org/docs/) tools need to be installed.

## Typical usage

Get initial Django project with Poetry managed virtual environment.

```
$ npm init django <project-name> [directory] -- --poetry
$ poetry install
$ poetry shell
$ ./manage.py migrate
$ ./manage.py runserver
```

## Options

### --asgi

Enables uvicorn based deployment

### --celery

[First-step with Django](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html) Celery configuration

Settings changed to use Redis as the Celery broker.

A celery worker could be started with the command:

```
$ celery -A <project-name> worker -l info
```

### --deploy

200+ lines single file ansible script to deploy to any Ubuntu-based VM. That's less than any deployment tutorial you can read about.

Compatible with many hosting solutions - DigitalOcean, Linode, Vultr, etc

* HTTP2/HTTPS with Letsencrypt certificates and Caddy server
* Systemd init scripts
* Postgresql fast connected over Unix socket.
* django-environ managed settings
* ASGI/Redis/Celery enabled if requested

```
# Initial server provision
$ ansible-playbook -i example.com, -u root --ask-vault-pass deploy.yml

# Refresh existing installation (without .env changes)
$ ansible-playbook -i example.com, -u root --tags=update deploy.yml
```

### --deploy-vault-pass

The password to manage deployment secrets. If no option is provided the password would be requested from console input.

### --poetry

Add `pyproject.toml` with all required project dependencies

### --redis

Enable Redis cache

### --rest

Add `django-rest-framework` dependency and enables SchemaView

### --user

Custom user model, forms and admin.

### --web

Modern ECMAScript and SASS build pipeline with Rollup.

Add `components/index.js` and `components/my-component` Web Component sample. Result Javascript and CSS compiled to the configured Django `static/` directory

```
$ npm run build # dev and minified build

$ npm run watch # continuously watch and rebuild dev version

$ npm run eslint  # code style check
```

## --all

Demo project with all features enabled

## Documentation

The list of links to software documentation to learn more about the technologies integrated into this minimal django project template:

[Ansible](https://docs.ansible.com/ansible/latest/index.html), [Babel](https://babeljs.io/docs/en/), [Caddy](https://caddyserver.com/docs/), [Celery](https://docs.celeryproject.org/en/stable/), [Dart Sass](https://sass-lang.com/documentation), [Django](https://docs.djangoproject.com/en/3.1/), [Django-environ](https://django-environ.readthedocs.io/en/latest/), [Django-redis](https://github.com/jazzband/django-redis), [Django RestFramework](https://www.django-rest-framework.org/), [ESLint](https://eslint.org/docs/user-guide/configuring/), [Gunicorn](https://docs.gunicorn.org/en/latest/configure.html), [NPM](https://docs.npmjs.com/), [Poetry](https://python-poetry.org/docs/), [PostgreSQL](https://www.postgresql.org/docs/), [Redis](https://redis.io/documentation), [Rollup.js](https://rollupjs.org/guide/en/), [Uvicorn](https://www.uvicorn.org/), [Systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html) [Unit Files](https://www.freedesktop.org/software/systemd/man/systemd.unit.html) and [Logging](https://www.freedesktop.org/software/systemd/man/journalctl.html), [Viewflow](https://docs-next.viewflow.io/), [Web Components](https://developer.mozilla.org/en-US/docs/Web/Web_Components),
