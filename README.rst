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

Viewflow works with Django 1.8/1.9/1.10/1.11

Viewflow 1.x.x  going to be supported till Django 1.8 lifetime (April 2018)


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
admin and allows you to build business applications. It’s based on
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

1.0.0 2017-05-29
----------------

* Django 1.11 support
* Open-sourced Python 2.7 support
* Added APGL licence additional permissions (allows to link with commercial software)
* Localization added: German/French/Spainish/Korean/Chinese
* Improved task detail UI in frontend
* Frontend - task management menu fix
* `JobActivation.async` method renamed to `run_async`. Fix python 3.7 reserved word warning.  
* [PRO] New process dashboard view
* [PRO] Django-Guardian support for task object level permissions
* [PRO] Fixes and improvements in the flow chart rendering
