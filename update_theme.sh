#!/bin/sh

git submodule update
git submodule foreach git pull origin master

mkdir -p viewflow/static/viewflow/css
mkdir -p viewflow/static/viewflow/js


# bootstrap
cp -v theme/css/bootstrap.css viewflow/static/viewflow/css
cp -v theme/js/bootstrap.js viewflow/static/viewflow/js

# font awesome
mkdir -p viewflow/static/viewflow/fonts
cp -v theme/css/font-awesome.css viewflow/static/viewflow/css
cp -v theme/fonts/FontAwesome.otf viewflow/static/viewflow/fonts
cp -v theme/fonts/fontawesome-* viewflow/static/viewflow/fonts

# admin lte
cp -v theme/css/AdminLTE.css viewflow/static/viewflow/css
cp -v theme/js/AdminLTE/app.js viewflow/static/viewflow/js/AdminLte.js

# icheck
mkdir -p viewflow/static/viewflow/css/iCheck/minimal
mkdir -p viewflow/static/viewflow/js/iCheck
cp -v theme/css/iCheck/minimal/minimal.png viewflow/static/viewflow/css/iCheck/minimal
cp -v theme/js/plugins/iCheck/icheck.js viewflow/static/viewflow/js/iCheck


# jquery.inputmask
mkdir -p viewflow/static/viewflow/js/
cp -vR theme/js/plugins/input-mask/ viewflow/static/viewflow/js/
