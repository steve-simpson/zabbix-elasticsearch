.. _getting_started:

Getting Started
===============
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

Prerequisites
-------------
You will however need to be running Zabbix Server 3.2+ and Elasticsearch 7+. Zabbix Server should be able to communicate with the Elasticsearch cluster over the Network

Elasticsearch
`````````````
Full Elasticsearch setup goes well beyond the scope of this project, however an Elasticsearch cluster needs to be online and reachable before continuing. For development purposes you may wish to use the `elasticsearch docker image`_ or if docker isn't your thing you can use this `Vagrant box`_. 

**Disclaimer** - The above Vagrant box is not an official Elasticsearch build, this is something I threw together while evaluating Elasticsearch.


.. _elasticsearch docker image: https://hub.docker.com/_/elasticsearch
.. _Vagrant box: https://app.vagrantup.com/stevesimpson/boxes/elasticsearch


::

	# Note: Pulling an images requires using a specific version number tag. The latest tag is not supported.

	docker pull elasticsearch:7.3.2
	docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:7.3.2

	# Ensure Elasticsearch is up and reachable
	curl -X GET "http://localhost:9200/_cluster/health?pretty"
	{
	  "cluster_name" : "docker-cluster",
	  "status" : "green",
	  "timed_out" : false,
	  "number_of_nodes" : 1,
	  "number_of_data_nodes" : 1,
	  "active_primary_shards" : 0,
	  "active_shards" : 0,
	  "relocating_shards" : 0,
	  "initializing_shards" : 0,
	  "unassigned_shards" : 0,
	  "delayed_unassigned_shards" : 0,
	  "number_of_pending_tasks" : 0,
	  "number_of_in_flight_fetch" : 0,
	  "task_max_waiting_in_queue_millis" : 0,
	  "active_shards_percent_as_number" : 100.0
	}

Zabbix
``````
As mentioned above 