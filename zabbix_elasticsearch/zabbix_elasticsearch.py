"""
Zabbix Monitoring for Elasticsearch
"""


import json
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
            'nodes',
            'cat',
            '_all'
        ]
    )
    parser.add_argument(
        "--endpoint",
        help="specify API",
        choices=[
            'stats',
            'health',
            'shards',
            '_ilm/explain'
        ]
    )
    parser.add_argument(
        "--metric",
        help="specifiy metric"
    )
    # The below options will be used as parameters in the API call.
    parser.add_argument(
        "--parameters",
        help="Seprated parmaters to be used with the API call. ';' seperator. "
        "Example format=json;bytes=kb;index=index_name;nodes=nodes_1,node_2"
    )
    parser.add_argument(
        "--nodes",
        help="comma seperated list of nodes. Limit the returned data to given nodes"
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
            datefmt='%d/%m/%Y %H:%M:%S',
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
        ],
        'cat': [
            'shards'
        ],
        '_all': [
            '_ilm/explain'
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

    def node_discovery(self, response):
        """Discover nodes"""
        returned_data = {'data': []}

        for key, value in response['nodes'].items():
            returned_data['data'].append({
                '{#NODE_ID}': key,
                '{#NODE_NAME}': value['name'],
                '{#NODE_IP}': value['ip']
            })
        return json.dumps(returned_data)

    def index_discovery(self, response):
        """Discover Indices"""
        returned_data = {'data': []}

        for key, value in response['indices'].items():
            returned_data['data'].append({
                '{#INDEX_NAME}': key,
                '{#INDEX_UUID}': value['uuid'],
            })
        return json.dumps(returned_data)

    def convert_flatten(self, dictionary, parent_key='', sep='.'):
        """
        Code to convert dict to flattened dictionary.
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

    def shards_per_node(self, api_response, nodes):
        """Get count of all shards that match the given node"""
        count = 0
        for item in api_response:
            if item['node'] in nodes:
                count += 1
        return count

    def ilm_explain(self, api_response):
        """Loop through the index response and look for ERROR steps. Return 1 is any ERRORS found"""
        for index in api_response["indices"].keys():
            print(index)
            if api_response["indices"][index]["managed"] == "true":
                print("true")
                if api_response["indices"][index]["step"] == "ERROR":
                    print("error")
                    res = 1
                    return res
                else:
                    print("no error")
                    res = 0
                    return res

    def send_requests(self, args):
        """GET METRICS"""

        api_call = getattr(self.es_config, args.api)
        print(api_call)

        if args.parameters:
            api_parameters = dict(
                param.split("=")
                for param in args.parameters.split(";")
            )
            if not api_parameters['format']:
                api_parameters['format'] = "json"
        else:
            api_parameters = dict({"format": "json"})

        try:
            api_response = getattr(api_call, args.endpoint)(**api_parameters)
            print(api_response)
        # Elasticsearch serialization error
        except exceptions.SerializationError:
            logging.error("SerializationError. "
                          "Check that %s is a valid format for this API.",
                          api_parameters['format']
                          )
            sys.exit(1)
        except:
            logging.error("Problem calling API. Check CLI arguments and parameters then try again")
            sys.exit(1)

        try:
            # Handle "null" metrics
            if args.metric is None:
                logging.error("'--metric' has not been specified. Terminating")
                sys.exit(1)
            # Discovery
            elif args.metric == "node_discovery" or args.metric == "index_discovery":
                logging.info("Running discovery...")
                response = getattr(self, args.metric)(api_response)
                return response
            # Get Metric
            elif args.metric == "shards_per_node":
                try:
                    response = self.shards_per_node(api_response, args.nodes)
                    return response
                except TypeError:
                    logging.error("Cannot iterate through response. "
                                  "Likley cause: '--nodes' has not been specified. Terminating")
                    sys.exit(1)
            elif args.metric == "ilm_explain":
                print("ilm_explain == true")
                try:
                    response = self.ilm_explain(api_response)
                    print(response)
                    return response
                except:
                    logging.error("ILM Explain Error")
                    sys.exit(1)
            else:
                response = self.convert_flatten(api_response)
                logging.info("'%s': %s", args.metric, response[args.metric])
                return response[args.metric]

        except KeyError:
            logging.error("KeyError: '%s' is not a valid metric for the '%s' endpoint. "
                          "Terminating", args.metric, args.endpoint)
            sys.exit(1)


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


if __name__ == "__main__":
    main()
