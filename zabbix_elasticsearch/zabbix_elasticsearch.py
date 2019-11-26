"""
Zabbix Monitoring for Elasticsearch
"""


import sys
import logging
import argparse
from distutils.util import strtobool
import configparser
from collections import MutableMapping
from elasticsearch import Elasticsearch, exceptions
import urllib3


def parse_conf(argv=None):
    """Read configuration parameters from config file and configure argparse"""
    # Do argv default this way, as doing it in the functional
    # declaration sets it at compile time.

    if argv is None:
        argv = sys.argv

    # Parse any conf_file specification
    # We make this parser with add_help=False so that
    # it doesn't parse -h and print help.
    conf_parser = argparse.ArgumentParser(
        description=__doc__, # printed with -h/--help
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
    )
    conf_parser.add_argument(
        "-c",
        "--conf_file",
        help="Specify path to config file",
        metavar="FILE"
    )
    args, remaining_argv = conf_parser.parse_known_args()

    defaults = {}

    if args.conf_file:
        try:
            with open(args.conf_file):
                config = configparser.ConfigParser()
                config.read([args.conf_file])
        except IOError as err:
            print(err)
            sys.exit(1)

        # Not the cleanest solution.
        # Flattens the config into a single argparse namespace
        try:
            defaults.update(dict(config.items("GLOBAL")))
            defaults.update(dict(config.items("ELASTICSEARCH")))
        except configparser.NoSectionError as err:
            print(f"Configuration Error: {err}")
            sys.exit(1)

    # Parse rest of arguments
    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[conf_parser],
        description='Elasticsearch Monitoring for Zabbix Server'
        )
    parser.set_defaults(**defaults)
    parser.add_argument(
        "--api",
        help="specify API",
        choices=[
            'cluster',
            'indices',
            'nodes'
        ]
    )
    parser.add_argument(
        "--endpoint",
        help="specify API",
        choices=[
            'stats',
            'health',
        ]
    )
    parser.add_argument(
        "--metric",
        help="specifiy metric"
    )
    parser.add_argument(
        "--nodes",
        help="limit results to a particular node. Multiple nodes should be comma seperated"
    )
    # These options are specified in the config file but can be overridden on the CLI
    parser.add_argument(
        "--logstdout",
        help="Enable logging to stdout",
    )
    parser.add_argument(
        "--logdir",
        help="Specifiy log directory",
    )
    parser.add_argument(
        "--logfilename",
        help="Specify logfile name"
    )
    parser.add_argument(
        "--loglevel",
        help="set log level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    )
    parser.add_argument(
        "--hosts",
        help="comma seperated list of hosts",
    )
    args = parser.parse_args(remaining_argv)
    return args

def configure_logging(level, logstdout, logdir, logfilename):
    """Configure Logging"""
    try:
        log_level = getattr(logging, level.upper())
    except AttributeError as err:
        logging.basicConfig(
            stream=sys.stdout,
            format='[%(asctime)s] %(levelname)s %(message)s',
            datefmt='%d/%m/%Y %I:%M:%S',
            level='INFO'
        )
        logging.error(err)
        sys.exit(1)

    if logstdout.lower() == 'true':
        # Log to stdout
        logging.basicConfig(
            stream=sys.stdout,
            format='[%(asctime)s] %(levelname)s %(message)s',
            datefmt='%d/%m/%Y %I:%M:%S',
            level=log_level
        )
    elif logstdout.lower() == 'false':
        # Attempt to write to logfile.
        # If file does not exist, write to stdout and exit
        logfile = f"{logdir}{logfilename}"
        try:
            with open(logfile, 'a') as file:
                pass
            file.close()
            logging.basicConfig(
                filename=logfile,
                format='[%(asctime)s] %(levelname)s %(message)s',
                datefmt='%d/%m/%Y %I:%M:%S',
                level=log_level
            )
        except PermissionError:
            logging.basicConfig(
                stream=sys.stdout,
                format='[%(asctime)s] %(levelname)s %(message)s',
                datefmt='%d/%m/%Y %I:%M:%S',
                level=log_level
            )
            logging.error("Log file: %s can not be written, permission denied. \
                Ensure log directory and log file are writable. Closing", logfile)
            sys.exit(1)

    return logging

def validate_args(args):
    """Validate the CLI arguments"""
    choices_matrix = {
        'cluster': [
            'stats',
            'health'
        ],
        'indices': [
            'stats'
        ],
        'nodes': [
            'stats'
        ]
    }

    # Lookup the args endpoint to ensure it is valid for the requested api
    if args.endpoint not in choices_matrix.get(args.api, args.endpoint):
        logging.error("'%s' is not a valid endpoint for the '%s' api. "
                      "Terminating", args.endpoint, args.api)
        sys.exit(1)

class ESWrapper:
    """Functions to call Elasticsearch API"""
    def __init__(self, args):
        # Disable warning about SSL certs
        if args.disable_ssl_warning.lower() == 'true':
            urllib3.disable_warnings()

        self.es_configuration = {}

        # Convert hosts to python list
        self.es_hosts = args.hosts.split(",")
        self.es_configuration["hosts"] = self.es_hosts
        self.es_configuration["scheme"] = args.httpscheme
        self.es_configuration["port"] = int(args.port)

        self.es_configuration["sniff_on_start"] = args.sniffonstart.lower()
        self.es_configuration["sniff_on_connection_fail"] = args.sniffonconnectionfail.lower()
        self.es_configuration["sniffer_timeout"] = int(args.sniffertimeout)

        # Build SSL options if SSL_enabled
        if strtobool(args.use_ssl):
            try:
                self.es_configuration["use_ssl"] = True
                self.es_configuration["verify_certs"] = strtobool(args.verify_ssl_certs)
                self.es_configuration["ssl_show_warn"] = strtobool(args.ssl_show_warn)
            except ValueError as err:
                logging.error("%s. Terminating", err)
                sys.exit(1)
        else:
            self.es_configuration["es_use_ssl"] = False

        # Build authentication options if using authenticated url
        try:
            if strtobool(args.httpauth):
                self.es_configuration["http_auth"] = (args.authuser, args.authpassword)
        except ValueError as err:
            logging.error("%s. Terminating", err)
            sys.exit(1)

        try:
            self.es_config = Elasticsearch(**self.es_configuration)
        except exceptions.TransportError as err:
            logging.error(err)
            sys.exit(1)

    def convert_flatten(self, dictionary, parent_key='', sep='.'):
        """
        Code to convert ini_dict to flattened dictionary.
        Default seperater '.'
        """
        items = []
        for key, value in dictionary.items():
            new_key = parent_key + sep + key if parent_key else key

            if isinstance(value, MutableMapping):
                items.extend(self.convert_flatten(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
        return dict(items)

    def send_requests(self, args):
        """GET CLUSTER METRICS"""
        api_call = getattr(self.es_config, args.api)
        if args.nodes:
            response = getattr(api_call, args.endpoint)(node_id=args.nodes)
        else:
            response = getattr(api_call, args.endpoint)()
        flattened_response = self.convert_flatten(response)

        # Handle "null" metrics
        if args.metric is None:
            logging.error("'--metric' has not been specified. Terminating")
            sys.exit(1)

        try:
            return flattened_response[args.metric]
        except KeyError:
            logging.error("KeyError: '%s' is not a valid metric for the '%s' endpoint. "
                          "Terminating", args.metric, args.endpoint)
            sys.exit(1)
        logging.info("'%s': %s. CLOSING", args.metric, flattened_response[args.metric])
        sys.exit(0)


def main(argv=None):
    """Main Execution path"""
    if argv is None:
        argv = sys.argv

    args = parse_conf()
    configure_logging(args.loglevel, args.logstdout, args.logdir, args.logfilename)
    validate_args(args)
    es_wrapper = ESWrapper(args)

    try:
        result = es_wrapper.send_requests(args)
        print(result)
        sys.exit(0)
    except AttributeError as err:
        logging.error(err)
        sys.exit(1)

    # if args.api == "cluster_stats":
    #     ESWrapper(args).cluster_stats(args.metric)
    # elif args.api == "cluster_health":
    #     ESWrapper(args).cluster_health(args.metric)
    # else:
    #     logging.error("'--api' must be specified")
    #     sys.exit(1)


if __name__ == "__main__":
    main()
