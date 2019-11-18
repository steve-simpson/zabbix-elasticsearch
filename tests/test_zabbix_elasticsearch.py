""" Tests """

from zabbix_elasticsearch.zabbix_elasticsearch import parse_conf


class TestArgParse:
    """ Test that default config file is read """

    def test_parse_conf(self):
        """ Parse default arguments and check for the defaults values in config file """
        args = parse_conf()
        # Ensure using the default configuration
        assert args.conf_file == "conf/default.conf"
        # Ensure loglevel is set correctly
        assert args.loglevel == 'INFO'
