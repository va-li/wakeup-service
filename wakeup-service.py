import time
import os
import re
import ipaddress
import json
import logging
import configparser

from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import WSGIServer
from flask import Flask, render_template, request, jsonify
from wakeonlan import send_magic_packet
from ping3 import ping

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read configuration
config = configparser.ConfigParser()
config.read('config.ini')

class Machine:
    def __init__(self, ip_address, mac_address):
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.last_successful_ping_time = None

    def ping(self) -> bool:
        response_time = ping(self.ip_address, timeout=1)
        if response_time is not None:
            self.last_successful_ping_time = time.time()
            return True
        return False

    def wake(self):
        send_magic_packet(self.mac_address)

# Initialize the machine object using the configuration file
machine = Machine(config.get('Machine', 'ip_address'), config.get('Machine', 'mac_address'))
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html',
                           ip_address=machine.ip_address,
                           mac_address=machine.mac_address,
                           last_successful_ping_time=machine.last_successful_ping_time)

@app.route("/ping", methods=['POST'])
def ping_machine():
    try:
        data = request.get_json()
        new_ip_address = str(ipaddress.ip_address(data['ip_address']))

        if new_ip_address != machine.ip_address:
            machine.ip_address = new_ip_address
            logging.info(f'IP address updated to: {machine.ip_address}')

        ping_successful = machine.ping()
        logging.info(f'Pinged, last successful ping time: {machine.last_successful_ping_time}')

        return jsonify(ip_address=machine.ip_address,
                       last_successful_ping_time=machine.last_successful_ping_time,
                       ping_successful=ping_successful)

    except ValueError as e:
        logging.error(f'Invalid IP address entered: {data["ip_address"]}')
        return jsonify(error=str(e)), 400

@app.route("/wol", methods=['POST'])
def wake_on_lan():
    try:
        data = request.get_json()
        new_mac_address = data['mac_address']

        if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", new_mac_address.lower()):
            if new_mac_address != machine.mac_address:
                machine.mac_address = new_mac_address
                logging.info(f'MAC address updated to: {machine.mac_address}')
        else:
            raise ValueError("Invalid MAC address format.")

        machine.wake()
        logging.info(f'Wake-on-LAN packet sent to {machine.mac_address}')

        return jsonify(mac_address=machine.mac_address,
                       last_successful_ping_time=machine.last_successful_ping_time)

    except ValueError as e:
        logging.error(f'Invalid MAC address entered: {new_mac_address}')
        return jsonify(error=str(e)), 400

if __name__ == "__main__":
    host = config.get('Server', 'host')
    port = config.getint('Server', 'port')
    logging.info(f'Starting server on http://{host}:{port}...')
    http_server = WSGIServer((host, port), app)
    http_server.serve_forever()
