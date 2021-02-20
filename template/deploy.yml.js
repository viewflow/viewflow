/* eslint-env node */
/* eslint max-len: ["error", { "code": 500 }] */
const render = (ctx) => `# Deploy test project to a generic Ubuntu host.
# Usage:
#     poetry run ansible-playbook -i example.com, -u root --ask-vault-pass deploy.yml
# Refresh existing installation (without .env changes):
#     poetry run ansible-playbook -i example.com, -u root --tags=update deploy.yml
- hosts: all
  become: true
  environment:
    LANG: "en_US.UTF-8"
    LC_ALL: "en_US.UTF-8"
  vars:
    ansible_ssh_pipelining: 1
    domain_name: "{{ ansible_host }}"
    project_name: "{{ domain_name.split('.').0 }}"
    project_user: "django-{{ project_name }}"
  handlers:
    - name: caddy | restart
      service: name=caddy state=restarted
    - name: gunicorn | restart
      service: name=django-{{ project_name }} state=restarted${ctx.celery ?`
    - name: celery | restart
      service: name=celery-{{ project_name }} state=restarted
    - name: celerybeat | restart
      service: name=celerybeat-{{ project_name }} state=restarted`:''}
  tasks:
    - name: "system | Add caddy repository"
      apt_repository:
        repo: deb [trusted=yes] https://apt.fury.io/caddy/ /

    - name: "system | install system wide dependencies"
      package:
        state: present
        name:
          - rsync
          - postgresql
          - caddy
          - python3-psycopg2   # Required by ansible to create pg db/user.
          - python3-setuptools # Required by ansible to use pip.
          - python3-pip        # Actual pip for ansible.
          - python3-venv       # Allows poetry create virtual environment
          - python3-dev        # Setup the python dev package${ctx.celery || ctx.redis ? `
          - redis`: ''}

    - name: "system | create system user"
      user: name="{{ project_user }}" group=caddy system=yes create_home=false

    - name: "system | install poetry"
      pip:
        name: poetry
        executable: pip3
      register: poetry

    - name: "system | configure poetry to use local dir for virtual environments"
      command: "poetry config virtualenvs.in-project true"
      when: poetry.changed

    - name: "web | setup caddyfile"
      copy:
        content: |
          import *.caddy
        dest: "/etc/caddy/Caddyfile"
        mode: "a+r"
      notify:
        - caddy | restart

    - name: "web | caddy configuration"
      copy:
        content: |
          www.{{ domain_name }} {
            redir https://{{ domain_name }}{uri}
          }
          {{ domain_name }} {
            encode gzip
            header Strict-Transport-Security "max-age=31536000; preload"
            @excludeDirs {
              not path /static/* /media/*
            }
            reverse_proxy @excludeDirs unix//var/run/django-{{ project_name }}/gunicorn.sock
            file_server {
              root /var/www/{{ domain_name }}/
            }
          }
        mode: "a+r"
        dest: "/etc/caddy/{{ project_name }}.caddy"
      notify:
        - caddy | restart

    - name: "web | setup gunicorn service"
      copy:
        content: |
          [Unit]
          Description=Django {{ domain_name }} daemon
          Requires=django-{{ project_name }}.socket
          After=network.target
          [Service]
          ExecReload=/bin/kill -s HUP $MAINPID
          ExecStart=/srv/{{ domain_name }}/.venv/bin/gunicorn \\
              --access-logfile - --error-logfile - --capture-output \\
              --max-requests=2000 --max-requests-jitter=400 ${ctx.asgi?' -k uvicorn.workers.UvicornWorker':''} \\
              --workers={{ ansible_facts['processor_nproc']*2+1}} ${ctx.project}.${ctx.asgi ? 'asgi': 'wsgi'}:application
          Group=caddy
          KillMode=mixed
          ProtectSystem=full
          TimeoutStopSec=5
          Type=notify
          User={{ project_user }}
          WorkingDirectory=/srv/{{ domain_name }}
          [Install]
          WantedBy=multi-user.target
        dest: /etc/systemd/system/django-{{ project_name }}.service
        mode: "a+r"
      notify:
        - gunicorn | restart

    - name: "web | setup gunicorn socket"
      copy:
        content: |
          [Unit]
          Description=Django test socket
          [Socket]
          ListenStream=/run/django-test/gunicorn.sock
          [Install]
          WantedBy=sockets.target
        dest: /etc/systemd/system/django-{{ project_name }}.socket
      notify:
        - gunicorn | restart

    - name: "project | synchronize source code"
      synchronize:
        src: ../
        dest: /srv/{{ domain_name }}/
        delete: true
        use_ssh_args: true
        rsync_opts:
          - "--filter=- .*"
          - "--filter=- *.pyc"
          - "--filter=- *.sqlite3"
          - "--filter=- node_modules/"
      register: source
      notify:
        - gunicorn | restart${ctx.celery ? `
        - celery | restart
        - celerybeat | restart`:''}
      tags: update

    - name: "project | install python dependencies with poetry"
      shell: "poetry install -E production --no-root --no-dev"
      args:
        chdir: /srv/{{ domain_name }}/
      tags: update
      when: source.changed

    - name: "database | create postgresql user"
      become_user: postgres
      postgresql_user: name="{{ project_user }}"

    - name: "database | create postgresql database"
      become_user: postgres
      postgresql_db: name="{{ project_user }}" owner="{{ project_user }}"
${ctx.celery ?`
    - name: celery | common configuration
      copy:
        content: |
          CELERYD_NODES="{{ project_name }}"
          CELERY_BIN="/srv/{{ domain_name }}/.venv/bin/celery"
          CELERY_APP="${ctx.project}"
          CELERYD_MULTI="multi"
          CELERYD_OPTS="--time-limit=300 --concurrency=2 -Q celery-{{ domain_name }}"
          CELERYD_PID_FILE="/run/celery-{{ project_name }}/%n.pid"
          CELERYD_LOG_FILE="/var/log/celery-{{ project_name }}/%n%I.log"
          CELERYD_LOG_LEVEL="INFO"
          CELERYBEAT_DB_FILE="/run/celery-{{ project_name }}/beat"
          CELERYBEAT_PID_FILE="/run/celery-{{ project_name }}/beat.pid"
          CELERYBEAT_LOG_FILE="/var/log/celery-{{ project_name }}/beat.log"
        dest: /etc/default/celery-{{ project_name }}.conf
      notify:
        - celery | restart
        - celerybeat | restart

    - name: celery | setup  service
      copy:
        content: |
          [Unit]
          Description=Celery Service
          After=network.target
          [Service]
          EnvironmentFile=/etc/default/celery-{{ project_name }}.conf
          ExecStart=/bin/sh -c '\${CELERY_BIN} multi start \${CELERYD_NODES} -A \${CELERY_APP} \\
              --pidfile=\${CELERYD_PID_FILE} --logfile=\${CELERYD_LOG_FILE} \\
              --loglevel=\${CELERYD_LOG_LEVEL} \${CELERYD_OPTS}'
          ExecStop=/bin/sh -c '\${CELERY_BIN} multi stopwait \${CELERYD_NODES} \\
              --pidfile=\${CELERYD_PID_FILE}'
          ExecReload=/bin/sh -c '\${CELERY_BIN} multi restart \${CELERYD_NODES} -A \${CELERY_APP} \\
              --pidfile=\${CELERYD_PID_FILE} --logfile=\${CELERYD_LOG_FILE} \\
              --loglevel=\${CELERYD_LOG_LEVEL} \${CELERYD_OPTS}'
          Group=caddy
          LogsDirectory=celery-{{ project_name }}
          ProtectSystem=full
          RuntimeDirectory=celery-{{ project_name }}
          Type=forking
          User={{ project_user }}
          WorkingDirectory=/srv/{{ domain_name }}/
          [Install]
          WantedBy=multi-user.target
        dest: /etc/systemd/system/celery-{{ project_name }}.service
      notify:
        - celery | restart

    - name: Setup celery beat service
      copy:
        content: |
          [Unit]
          Description=Celery Beat Service
          After=network.target
          [Service]
          EnvironmentFile=/etc/default/celery-{{ project_name }}.conf
          ExecStart=/bin/sh -c '\${CELERY_BIN} beat -A \${CELERY_APP} --pidfile=\${CELERYBEAT_PID_FILE} \\
              --logfile=\${CELERYBEAT_LOG_FILE} --loglevel=\${CELERYD_LOG_LEVEL} \\
              -s \${CELERYBEAT_DB_FILE}'
          Group=caddy
          LogsDirectory=celery-{{ project_name }}
          ProtectSystem=full
          RuntimeDirectory=celery-{{ project_name }}
          Type=simple
          User={{ project_user }}
          WorkingDirectory=/srv/{{ domain_name }}/
          [Install]
          WantedBy=multi-user.target
        dest: /etc/systemd/system/celerybeat-{{ project_name }}.service
        mode: "a+r"
      notify:
        - celerybeat | restart

    - name: celery | configure log rotation
      copy:
        content: |
          /var/log/celery-{{ project_name }}/*.log {
            weekly
            missingok
            rotate 52
            compress
            delaycompress
            notifempty
            copytruncate
        dest: /etc/logrotate.d/celery-{{ project_name }}
`:''}
    - name: "django | create static dir"
      file: state=directory
        path=/var/www/{{ domain_name }}/static/
        owner="{{ project_user }}"
        group="caddy"
        mode="u=rx,g=rx"

    - name: "django | create media dir"
      file: state=directory
        path=/var/www/{{ domain_name }}/media/
        owner="{{ project_user }}"
        group="caddy"
        mode="u+rwx,g=rx"

    - name: "django | create/update .env file"
      copy:
        content: |
          ADMINS=kmmbvnr@gmail.com
          ALLOWED_HOSTS={{ domain_name }}
          DATABASE_URL=postgres:///django-{{ project_name }}
          DEBUG=0
          MEDIA_ROOT=/var/www/{{ domain_name }}/media/
          SECRET_KEY={{ secret_key }}
          STATIC_ROOT=/var/www/{{ domain_name }}/static/
        dest: "/srv/{{ domain_name }}/.env"
        owner: "{{ project_user }}"
        mode: "u+r"
      vars:
        secret_key: !vault |
${ctx.secretKeyVault}
      when: source.changed

    - name: "django | collect static files"
      shell: "poetry run ./manage.py collectstatic --noinput"
      args:
        chdir: /srv/{{ domain_name }}/
      when: source.changed
      tags: update

    - set_fact:
        project_user: "{{ project_user }}"  # to be available for become_user
      tags: update

    - file:
        name: /home/{{ project_user }}/.ansible/tmp  # to avoid ansible warning due become_user
        state: directory
        owner: '{{ project_user }}'
        mode: 'u+rwx'

    - name: "django | run migration"
      shell: "poetry run ./manage.py migrate --noinput"
      args:
        chdir: /srv/{{ domain_name }}/
      become_user: "{{ project_user }}"
      when: source.changed
      tags: update
`.replace(/[^\S\r\n]+$/gm, '');

exports.default = render;
