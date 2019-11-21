# Zabbix Elasticsearch

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/zabbix_elasticsearch) ![PyPI](https://img.shields.io/pypi/v/zabbix_elasticsearch) [![Build Status](https://travis-ci.org/steve-simpson/zabbix_elasticsearch.svg?branch=master)](https://travis-ci.org/steve-simpson/zabbix_elasticsearch)
![PyPI - License](https://img.shields.io/pypi/l/zabbix_elasticsearch) 

Simple Python wrappr around the Elasticsearch python module to provide metrics for consumption by Zabbix Agent. In time, this project may be expanded to provide monitoring for the whole Elastic Stack (Elasticsearch, Kibana, Logstash, Beats etc.)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

Despite the project name, you don't actually need Zabbix Server/Agent setup to run this project. You can "mock" Zabbix Agent using the CLI to see the metric required. See deployment for more info.

You will however need a connection to Elasticsearch in order to collect metrics. For development purposes you may wish to use the elasticsearch docker image here: `https://hub.docker.com/_/elasticsearch` or you can checkout `https://app.vagrantup.com/stevesimpson/boxes/elasticsearch` for my Vagrant setup. Either way, the Elasticsearch cluster needs to be online and reachable.

```
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
```

### Installing

Install the package using `pip`. Virtualenv is recommended.
```
pip install zabbix-elasticsearch
```

Copy the default configuration file to a destination of your choosing.The default options will work with an Elasticsearch "Cluster" running on "localhost".
```
cp <install_dir>/docs/default.conf <dest>

# Example using virtualenv, 'zabbix-elasticsearch'

mkdir -p /etc/zabbix-elasticsearch # Make new config directory
cp ~/.virtualenvs/zabbix-elasticsearch-test/docs/default.conf /etc/zabbix-elasticsearch/zabbix-elasticsearch.conf
```

That's it! Here's a usage example to grab the cluster status.  The `--api`, `--endpoint` and `--metric` options will be fully documented in time.
```
zabbix_elasticsearch -c /etc/zabbix-elasticsearch/zabbix-elasticsearch.conf --api cluster --endpoint stats --metric status
[19/11/2019 12:03:03] INFO GET http://localhost:9200/_nodes/_all/http [status:200 request:0.004s]
[19/11/2019 12:03:03] INFO GET http://172.17.0.2:9200/_cluster/stats [status:200 request:0.005s]
green
[19/11/2019 12:03:03] INFO 'status': green. CLOSING
```

As you can see we are logging to stdout, this can be changed to log to a file in the config. The important output here for Zabbix integration is the printed output "green". This will be used in a later Zabbix template.
## Running the tests

Test coverage is almost non exsitant. I'm hoping to change that soon! You can run `pytest` in the project root to run the pointless test if you like. Testing contributions most welcome :heavy_check_mark:

## Deployment

Coming Soon :construction:

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Steve Simpson** - *Project Owner*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* CI and Build with Travis CI
* Package hosted on PyPI 
* Thanks to the teams at both Elastic and Zabbix for providing excellent open source tools