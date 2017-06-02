===============
django-viewflow
===============

Reusable workflow library for Django, that helps to implement people collaboration software.

http://viewflow.io.


Viewflow takes best parts from two worlds. It is based on BPMN -
business process modeling and notation standard. And plays well with
django web development toolchain. BPMN provides a standard
notation readily understandable by all business stakeholders. Viewflow
bridging the gap between picture and executable, ready to use web
application.

.. image:: https://raw.githubusercontent.com/viewflow/viewflow/master/demo/shipment/doc/ShipmentProcess.png
   :width: 400px

After over than 10 years history of the BPMN standard, it contains
whole set of battle-proven primitives for all occasions, helps you to
describe all real life business process scenarios. Viewflow helps you
to build a bpmn diagram in code and keep business logic separate from
django forms and views code.

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

Django-Material 1.x branch going to be supported till Django 1.8 lifetime (April 2018)


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
