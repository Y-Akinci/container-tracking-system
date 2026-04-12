import argparse
import asyncio
import configparser
import json
import logging.handlers
import os
import sys
import time
import requests

from integration import mqtt, http
from simulation.profile import Profile


def init_logging(config):
    level = config['log'].get('level', 'info').upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.handlers.RotatingFileHandler("./simulator.log", maxBytes=200000, backupCount=1),
            logging.StreamHandler()
        ]
    )


def init(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config


def parse_arguments():
    # create the parser
    my_parser = argparse.ArgumentParser()
    # add optional arguments
    my_parser.add_argument('--config', '-c', default='configuration.ini',
                           help='configuration file, default "configuration.ini"')
    # add positional arguments
    my_parser.add_argument('file', help='the geojson file to use')
    args = my_parser.parse_args()
    return args.config, args.file


def get_points_from_file(file):
    geo_json_map = json.load(open(file))
    coord = geo_json_map['features'][0]['geometry']['coordinates'][3]
    # retrieve the points
    points = [(i[1], i[0]) for i in coord]
    return points


async def run_mqtt(route, mqtt_client):
    mqtt_client.connect()
    while not mqtt_client.is_connected():
        print("Waiting to connect ...")
        time.sleep(1)
    await mqtt_client.publish(route.get("name"), route.get("points"))


async def run_http(route, http_client):
    await http_client.send(route.get("name"), route.get("points"))


if __name__ == '__main__':
    try:
        config_file, my_file = parse_arguments()
        app_config = init(config_file)
        init_logging(app_config)
        simulation_profile = Profile(app_config)
        my_points = get_points_from_file(my_file)
        filename_with_suffix = os.path.basename(my_file)
        my_route_name = os.path.splitext(filename_with_suffix)[0]
        my_route = {
            "name": my_route_name,
            "points": my_points
        }
        if app_config.has_section('mqtt'):
            my_mqtt_client = mqtt.MqttClient(app_config, simulation_profile)
            asyncio.run(run_mqtt(my_route, my_mqtt_client))
        else:
            print("No 'mqtt' configuration found")
            if app_config.has_section('http'):
                my_http_client = http.HttpClient(app_config, simulation_profile)
                asyncio.run(run_http(my_route, my_http_client))
            else:
                print("No 'http' configuration found")
    except KeyboardInterrupt:
        # handle ^C keyboard interrupt in main loop
        sys.exit(0)
    except (requests.exceptions.HTTPError, ValueError) as err:
        print(err)
