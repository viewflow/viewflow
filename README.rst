===============
django-viewflow
===============

Reusable workflow library for Django http://viewflow.io.

Viewflow is the workflow library based on BPMN concepts. BPMN -
business process modeling and notations - is the wide adopted industry
standard for business process modeling. BPMN provides a standard
notation readily understandable by all business stakeholders. Viewflow
bridging the gap between picture and executable, ready to use web
application.

.. image:: https://raw.githubusercontent.com/viewflow/viewflow/master/demo/shipment/doc/ShipmentProcess.png
   :width: 400px

Demo: http://demo.viewflow.io

After over than 10 years history of the BPMN standard, it contains
whole set of battle-proven primitives for all occasions, helps you to
describe all real life business process scenarios. Viewflow helps you
to build a bpmn diagram in code and keep business logic separate from
django forms and views code.

.. image:: https://travis-ci.org/viewflow/viewflow.svg
   :target: https://travis-ci.org/viewflow/viewflow

.. image:: https://requires.io/github/viewflow/viewflow/requirements.svg?branch=master
   :target: https://requires.io/github/viewflow/viewflow/requirements/?branch=master

.. image:: https://coveralls.io/repos/viewflow/viewflow/badge.png?branch=master
   :target: https://coveralls.io/r/viewflow/viewflow?branch=master


Documentation
=============

Read the documentation at the `http://docs.viewflow.io/ <http://docs.viewflow.io/introduction.html>`_

License
=======
Viewflow is an Open Source project licensed under the terms of
the AGPL license - `The GNU Affero General Public License v3.0 <http://www.gnu.org/licenses/agpl-3.0.html>`_

Viewflow Pro has a commercial-friendly license allowing private forks
and modifications of Viewflow. You can find the commercial license terms in COMM-LICENSE.
Please see `FAQ <https://github.com/kmmbvnr/django-viewflow/wiki/Pro-FAQ>`_ for more detail.  


Latest changelog
================

0.10.1 - 2016-03-24
-------------------

* flow.Start().Permission no longer supports callable (there is Start.Available for that)
* Task.flow_task and Task.owner_permission fields length extended up to 255 to match django Permission.name
