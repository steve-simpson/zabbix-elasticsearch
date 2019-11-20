.. Zabbix Elasticsearch documentation master file, created by
   sphinx-quickstart on Wed Nov 20 10:09:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Zabbix Elasticsearch's documentation!
================================================
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started

Simple Python wrapper around the `Elasticsearch python module`_ to provide metrics for consumption by Zabbix Agent. In time, this project may be expanded to provide monitoring for the whole Elastic Stack (Elasticsearch, Kibana, Logstash, Beats etc.)


.. _Elasticsearch python module: https://github.com/elastic/elasticsearch-py


Compatibility
-------------
This is known to work with Zabbix 3.2+ and Elasticsearch 7+

Installation
------------
Install the ``zabbix-elasticsearch`` package with `pip
<https://pypi.python.org/pypi/zabbix-elasticsearch>`_::

    pip install zabbix-elasticsearch

Example Usage
-------------
See :ref:`getting_started`



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`