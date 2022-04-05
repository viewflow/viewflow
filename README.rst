===============
django-viewflow
===============

Viewflow is a lightweight reusable workflow library that helps to
organize people collaboration business logic in django applications.

In conjunction with django-material, they could be used as the
framework to build ready to use business applications in minutes.

http://viewflow.io.

.. image:: https://img.shields.io/pypi/v/django-viewflow.svg
    :target: https://pypi.python.org/pypi/django-viewflow

.. image:: https://travis-ci.org/viewflow/viewflow.svg
   :target: https://travis-ci.org/viewflow/viewflow

.. image:: https://requires.io/github/viewflow/viewflow/requirements.svg?branch=master
   :target: https://requires.io/github/viewflow/viewflow/requirements/?branch=master

.. image:: https://coveralls.io/repos/viewflow/viewflow/badge.png?branch=master
   :target: https://coveralls.io/r/viewflow/viewflow?branch=master

.. image:: https://img.shields.io/pypi/pyversions/django-viewflow.svg
    :target: https://pypi.python.org/pypi/django-viewflow

- Viewflow 1.1.x compatible with Django 1.8/1.9/1.10/1.11 (supported till Django 1.8 lifetime/April 2018)
- Viewflow 1.2.x compatible with Django 1.11/2.0 (supported till Django 1.11 lifetime/April 2020)
- Viewflow 1.3.x/1.4.x/1.5.x compatible with Django 1.11/2.0/2.1/2.2 (supported till Django 1.11 lifetime/April 2020)
- Viewflow 1.6.x/1.7.x compatible with Django 2.0/2.1/2.2/3.0/3.1 (supported till Django 2.0 lifetime/December 2020)
- Viewflow 1.8.x/1.9.x compatible with Django 2.1/2.2/3.0/3.1
- Viewflow 1.10.x compatible with Django 2.2/3.0/3.1/3.2/4.0

Introduction
============

.. image:: https://raw.githubusercontent.com/viewflow/viewflow/master/demo/shipment/doc/ShipmentProcess.png
   :width: 400px

Django web framework solves only technical problems related to the
client-server interaction on top of the stateless HTTP
protocol. Model-View-Template separation pattern helps to maintain
simple CRUD based logic. Viewflow is the library that offers an
additional layer of django web framework, allows explicitly specify
people's workflow and extracts collaboration logic from django views.

Viewflow layer is based on the BPMN - business process management and
notation standard. It is the graphical notation readily understandable
by all business stakeholders and software developers. Viewflow bridges
the gap between a picture as the software specification and the
working solution.

Django-Material frontend is the lightweight alternative to the django
admin and allows you to build business applications. It's based on
Google Material Design, that could be easily customized to your brand
colors. Django-Material takes care of site-wide navigation, complex
form construction, datagrids and CRUD functionality. Ready for fast
development of any CRM, ERP, Business Management Software.


Quick start
===========

5 minutes introduction `tutorial <http://docs.viewflow.io/viewflow_quickstart.html>`_


Demo
====

Viewflow comes with reference UI implementation on top of django-material project.

http://demo.viewflow.io

To checkout and run open source demo version locally, you need to have
`git <https://git-scm.com/>`_ and `tox
<https://tox.readthedocs.io/en/latest/>`_ tools installed.

.. code:: bash

    git clone https://github.com/viewflow/viewflow.git
    cd viewflow

    TOXENV=py36-dj111 tox -- python manage.py migrate --settings=demo.settings
    TOXENV=py36-dj111 tox -- python manage.py loaddata demo/helloworld/fixtures/helloworld/default_data.json --settings=demo.settings
    TOXENV=py36-dj111 tox -- python manage.py runserver --settings=demo.settings

Then, you can open http://127.0.0.1:8000 and login with `admin:admin` username/password pair.


Documentation
=============

Read the documentation at the `http://docs.viewflow.io/ <http://docs.viewflow.io/>`_


Cookbook
========

Advanced customization samples

https://github.com/viewflow/cookbook


Contribution
============

Please open an issue to discuss. before pushing any new functionality.

See also - `Contribution Agreement <./CONTRIBUTION.txt>`_



License
=======

Viewflow is an Open Source project licensed under the terms of the AGPL license - `The GNU Affero General Public License v3.0 <http://www.gnu.org/licenses/agpl-3.0.html>`_ with the Additional
Permissions described in `LICENSE_EXCEPTION <./LICENSE_EXCEPTION>`_


Viewflow Pro has a commercial-friendly license allowing private forks
and modifications of Viewflow. You can find the commercial license terms in COMM-LICENSE.
Please see `FAQ <https://github.com/kmmbvnr/django-viewflow/wiki/Pro-FAQ>`_ for more detail.  


Latest changelog
================

1.11.0 2021-04-05
-----------------

- Django 4.0 fixes
- Simplify frontend task model customization
