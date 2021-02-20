#!/usr/bin/env node

/* eslint-env node */
'use strict';

const {Vault} = require('ansible-vault');
const {nanoid} = require('nanoid');
const commander = require('commander');
const fs = require('fs');
const inquirer = require('inquirer');
const packageJson = require('./package.json');


async function main() {
  let projectName;
  let projectDir;

  const program = new commander.Command(packageJson.name)
      .version(packageJson.version)
      .arguments('<project-name> [directory]')
      .action((name, dir) => {
        projectName = name;
        projectDir = dir || name;
      })
      .option('--all', 'all features at once')
      .option('--asgi', 'enable asgi deployment  --todo--')
      .option('--celery', 'enable celery')
      .option('--deploy', 'single file Ansible deploy script for genetic VPS host')
      .option('--deploy-vault-pass', 'password to encode django secret')
      .option('--poetry', 'add pyproject.toml')
      .option('--redis', 'enable redis cache')
      .option('--rest', 'add django-restframework and schema view')
      .option('--user', 'custom user model definition')
      // .option('--viewflow', 'bootstrap viewflow project --todo--')
      .option('--web', 'rollup script to build js web components js and sass')
      .option('--social-auth', '--todo--')
      .parse(process.argv);

  const ctx = {
    'asgi': program.asgi || program.all,
    'celery': program.celery || program.all,
    'deploy': program.deploy || program.all,
    'makefile': program.makefile || program.all,
    'poetry': program.poetry || program.deploy || program.all,
    'project': projectName,
    'projectDir': projectDir,
    'redis': program.redis || program.all,
    'rest': program.rest || program.all,
    'user': program.user || program.all,
    'vagrant': program.vagrant || program.all,
    'web': program.js || program.all,
    // vars
    'secretKey': nanoid(50),
  };

  const logError = (err) => {
    if (err) {
      console.log(err);
    }
  };

  if (typeof ctx.project === 'undefined') {
    console.error('no project name given!');
    process.exit(1);
  }

  if (ctx.deploy && !program.deployVaultPass) {
    const answers = await inquirer
        .prompt([
          {
            type: 'password',
            message: 'Enter a vault password',
            name: 'password',
          },
        ]);

    program.deployVaultPass = answers.password;
  }

  if (ctx.deploy) {
    const vault = new Vault({password: program.deployVaultPass});
    ctx['secretKeyVault'] = await vault.encrypt(nanoid(50));
    ctx['secretKeyVault'] = ctx['secretKeyVault'].replace(/^(?!\s*$)/gm, '          ');
  }

  let template;
  fs.mkdirSync(`${ctx.projectDir}/${ctx.project}`, {recursive: true});

  // manage.py
  template = require('./manage.py.js').default;
  fs.writeFile(`${ctx.projectDir}/manage.py`, template(ctx), (err) => {
    logError(err);
    fs.chmodSync(`${ctx.projectDir}/manage.py`, 0o755);
  });

  // deploy.yml
  if (ctx.deploy) {
    template = require('./deploy.yml.js').default;
    fs.writeFile(`${ctx.projectDir}/deploy.yml`, template(ctx), (err) => logError);
  }

  // pyproject.toml.js
  if (ctx.poetry) {
    template = require('./pyproject.toml.js').default;
    fs.writeFile(`${ctx.projectDir}/pyproject.toml`, template(ctx), (err) => logError);
  }

  // project_name/__init__.py
  template = require('./project_name/__init__.py.js').default;
  fs.writeFile(`${ctx.projectDir}/${ctx.project}/__init__.py`, template(ctx), (err) => logError);

  // project_dir/settings.py
  template = require('./project_name/settings.py.js').default;
  fs.writeFile(`${ctx.projectDir}/${ctx.project}/settings.py`, template(ctx), (err) => logError);

  // project_dir/urls.py
  template = require('./project_name/urls.py.js').default;
  fs.writeFile(`${ctx.projectDir}/${ctx.project}/urls.py`, template(ctx), (err) => logError);

  // project_dir/wsgi.py
  template = require('./project_name/wsgi.py.js').default;
  fs.writeFile(`${ctx.projectDir}/${ctx.project}/wsgi.py`, template(ctx), (err) => logError);

  // project_name/asgi.py
  if (ctx.asgi) {
    template = require('./project_name/asgi.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/asgi.py`, template(ctx), (err) => logError);
  }

  // project_name/celery.py
  if (ctx.celery) {
    template = require('./project_name/celery.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/celery.py`, template(ctx), (err) => logError);
  }

  if (ctx.user) {
    fs.mkdirSync(`${ctx.projectDir}/${ctx.project}/users/`);

    template = require('./project_name/users/__init__.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/users/__init__.py`, template(ctx), (err) => logError);

    template = require('./project_name/users/admin.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/users/admin.py`, template(ctx), (err) => logError);

    template = require('./project_name/users/forms.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/users/forms.py`, template(ctx), (err) => logError);

    template = require('./project_name/users/managers.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/users/managers.py`, template(ctx), (err) => logError);

    template = require('./project_name/users/models.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/users/models.py`, template(ctx), (err) => logError);

    // migrations
    fs.mkdirSync(`${ctx.projectDir}/${ctx.project}/users/migrations/`);

    template = require('./project_name/users/migrations/__init__.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/users/migrations/__init__.py`, template(ctx), (err) => logError);

    template = require('./project_name/users/migrations/0001_initial.py.js').default;
    fs.writeFile(`${ctx.projectDir}/${ctx.project}/users/migrations/0001_initial.py`, template(ctx), (err) => logError);
  }

  if (ctx.deploy || ctx.web) {
    fs.mkdirSync(`${ctx.projectDir}/static/`);
  }

  if (ctx.web) {
    fs.mkdirSync(`${ctx.projectDir}/components/`);
    fs.mkdirSync(`${ctx.projectDir}/components/my-component/`);

    template = require('./package.json.js').default;
    fs.writeFile(`${ctx.projectDir}/package.json`, template(ctx), (err) => logError);

    template = require('./rollup.config.js.js').default;
    fs.writeFile(`${ctx.projectDir}/rollup.config.js`, template(ctx), (err) => logError);

    template = require('./project_name/components/index.js.js').default;
    fs.writeFile(`${ctx.projectDir}/components/index.js`, template(ctx), (err) => logError);

    template = require('./project_name/components/my-component/index.js.js').default;
    fs.writeFile(`${ctx.projectDir}/components/my-component/index.js`, template(ctx), (err) => logError);

    template = require('./project_name/components/my-component/index.scss.js').default;
    fs.writeFile(`${ctx.projectDir}/components/my-component/index.scss`, template(ctx), (err) => logError);
  }
}

main();
