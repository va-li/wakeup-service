import time
import os
import re
import ipaddress

from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import WSGIServer
from flask import Flask, render_template, request
from wakeonlan import send_magic_packet

class Machine:
    def __init__(self, ip_address, mac_address):
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.last_successful_ping_time = None

    def ping(self) -> bool:
        response = os.system("ping -c 1 " + self.ip_address)
        if response == 0:
            self.last_successful_ping_time = time.time()
        
        return response == 0
            
    def wake(self):
        send_magic_packet(self.mac_address)

machine = Machine('192.168.0.87', 'bc:ee:7b:8c:70:80')
app = Flask(__name__)

def unix_time_to_str(unix_time):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(unix_time))

@app.route("/")
def index():
    return render_template('index.html',
                           ip_address=machine.ip_address,
                           mac_address=machine.mac_address,
                           last_successful_ping_time=unix_time_to_str(machine.last_successful_ping_time))

@app.route("/ping", methods=['POST'])
def ping():
    # get the ip address from the form data and update the machine status
    
    ip_address_invalid = False
    try:
        machine.ip_address = str(ipaddress.ip_address(request.form['ip_address']))
        print(f'IP address updated to: {machine.ip_address}')
        # ping the machine and update the last successful ping time
        ping_successful = machine.ping()
        print(f'Pinged, last successful ping time: {machine.last_successful_ping_time}')
    except ValueError:
        ip_address_invalid = True
        print(f'Invalid IP address entered: {request.form["ip_address"]}')        
        ping_successful = False
    
    return render_template('index.html',
                           ip_address=machine.ip_address,
                           mac_address=machine.mac_address,
                           last_successful_ping_time=unix_time_to_str(machine.last_successful_ping_time),
                           ping_successful=ping_successful,
                           ip_address_invalid=ip_address_invalid)

@app.route("/wol", methods=['POST'])
def wake_on_lan():
    # get the mac address from the form data and update the machine status
    new_mac_address = request.form['mac_address']
    mac_address_invalid = False
    
    if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", new_mac_address.lower()):
        machine.mac_address = new_mac_address
        print(f'MAC address updated to: {machine.mac_address}')
    else:
        mac_address_invalid = True
        print(f'Invalid MAC address entered: {new_mac_address}')
    
    # send the wake-on-lan packet
    machine.wake()
    print(f'Wake-on-LAN packet sent to {machine.mac_address}')
    
    return render_template('index.html',
                           ip_address=machine.ip_address,
                           mac_address=machine.mac_address,
                           last_successful_ping_time=unix_time_to_str(machine.last_successful_ping_time),
                           mac_address_invalid=mac_address_invalid)

if __name__ == "__main__":
    host = '0.0.0.0'
    port = 8000
    print(f'Starting server on {host}:{port}...')
    http_server = WSGIServer((host, port), app)
    http_server.serve_forever()
