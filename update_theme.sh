#!/bin/sh

git submodule update
git submodule foreach git pull origin master

mkdir -p viewflow/static/viewflow/css
mkdir -p viewflow/static/viewflow/js


# bootstrap
cp -v submodules/theme/css/bootstrap.css viewflow/static/viewflow/css
cp -v submodules/theme/js/bootstrap.js viewflow/static/viewflow/js

# font awesome
mkdir -p viewflow/static/viewflow/fonts
cp -v submodules/theme/css/font-awesome.css viewflow/static/viewflow/css
cp -v submodules/theme/fonts/FontAwesome.otf viewflow/static/viewflow/fonts
cp -v submodules/theme/fonts/fontawesome-* viewflow/static/viewflow/fonts

# admin lte
cp -v submodules/theme/css/AdminLTE.css viewflow/static/viewflow/css
cp -v submodules/theme/js/AdminLTE/app.js viewflow/static/viewflow/js/AdminLte.js

# icheck
mkdir -p viewflow/static/viewflow/css/iCheck/minimal
mkdir -p viewflow/static/viewflow/js/iCheck
cp -v submodules/theme/css/iCheck/minimal/minimal.png viewflow/static/viewflow/css/iCheck/minimal
cp -v submodules/theme/js/plugins/iCheck/icheck.js viewflow/static/viewflow/js/iCheck


# jquery.inputmask
mkdir -p viewflow/static/viewflow/js/
cp -vR submodules/theme/js/plugins/input-mask/ viewflow/static/viewflow/js/



# choosen
mkdir -p   viewflow/static/viewflow/js/chosen viewflow/static/viewflow/css/chosen
cd submodules/chosen
grunt
git checkout package.json
cd ../..

cp submodules/chosen/public/chosen.jquery.js viewflow/static/viewflow/js/chosen
cp submodules/chosen/public/chosen.css  viewflow/static/viewflow/css/chosen
cp submodules/chosen/public/chosen-sprite.png  viewflow/static/viewflow/css/chosen
cp submodules/chosen/public/chosen-sprite@2x.png  viewflow/static/viewflow/css/chosen
