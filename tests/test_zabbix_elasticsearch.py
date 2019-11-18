""" Tests """

import argparse
from zabbix_elasticsearch.zabbix_elasticsearch import parse_conf


class TestZabbixElasticsearch:
    """ Test Zabbix Elasticsearch"""

    def test_argparse_object(self):
        """ Simple test that asserts that 'args' is an argparse object """
        args = parse_conf()
        assert isinstance(args, argparse.Namespace)
