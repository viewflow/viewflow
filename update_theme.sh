#!/bin/sh

git submodule update
git submodule foreach git pull origin master

mkdir -p viewflow/static/viewflow/css
mkdir -p viewflow/static/viewflow/js


# bootstrap
cp -v theme/css/bootstrap.css viewflow/static/viewflow/css
cp -v theme/js/bootstrap.js viewflow/static/viewflow/js


# admin lte
cp -v theme/css/AdminLTE.css viewflow/static/viewflow/css
cp -v theme/js/AdminLTE/app.js viewflow/static/viewflow/js/AdminLte.js

# icheck
mkdir -p viewflow/static/viewflow/css/iCheck/minimal
mkdir -p viewflow/static/viewflow/js/iCheck
cp -v theme/css/iCheck/minimal/minimal.png viewflow/static/viewflow/css/iCheck/minimal
cp -v theme/js/plugins/iCheck/icheck.js viewflow/static/viewflow/js/iCheck