#!/bin/sh

git submodule update
git submodule foreach git pull origin master

# bootstrap
cp -v theme/css/bootstrap.css viewflow/static/viewflow/css
cp -v theme/js/bootstrap.js viewflow/static/viewflow/js


# admin lte
cp -v theme/css/AdminLTE.css viewflow/static/viewflow/css
cp -v theme/js/AdminLTE/app.js viewflow/static/viewflow/js/AdminLte.js
