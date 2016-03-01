=============
Viewflow Demo
=============

See live at: http://demo.viewflow.io or checkout and run:

.. code-block:: shell

    tox migrate
    tox loaddata tests/helloworld/fixtures/default_data.json
    tox loaddata tests/shipment/fixtures/default_data.json
    tox runserver

And get access on http://127.0.0.1:8000


* HelloWorld_  - Viewflow introduction sample
* Shipment_ - Automate shipment process for ecommerce website
* `Dynamic split`_ -  Custom flow node example

.. _HelloWorld: helloworld/
.. _Shipment: shipment/
.. _`Dynamic split`: customnode/


Standalone demo projects
========================

* Ecommerce_ - Delivery department automation with viewflow and Django Cartridge Ecommerce
* Customization_ - Custom auth model and django-guardian for object level permissions, no viewsite

.. _Ecommerce: https://github.com/kmmbvnr/viewflow-demo/tree/master/ecommerce
.. _Customization: https://github.com/kmmbvnr/viewflow-demo/tree/master/customauth
