# Wakeup Service

Wakes up my _beefy_ desktop computer from my Raspberry Pi with a Wake-on-LAN packet.

Why? The desktop computer has an idle load of ~80W. The Raspberry Pi has an idle load of less than 5W. Quick calculation: 80 Watts * 24 hours * 365 days = (80/1000)*24*365 kWh = 700,8 kWh per year. That would be lot of electricity wasted.

## Usage

Goto [http://10.64.0.4:8000/](http://10.64.0.4:8000/) to ping or wake up the computer.

### Notes

- The Raspberry Pi is connected to the same home network as the desktop computer.
- The Raspberry Pi is also in the wiregurad VPN network (hence the `10.64.0.4` IP address).

## Setup

1. Create a new user for the service on the Raspberry Pi

    ```bash
    sudo useradd -r -s /bin/false wakeup_service
    ```

2. Create a directory for the service, but make it owned by your user (here: `gir`)

    ```bash
    sudo mkdir /usr/local/lib/wakeup-service
    sudo chown gir:gir /usr/local/lib/wakeup-service/
    ```

3. Create a virtual environment for the service

    ```bash
    python3 -m venv /usr/local/lib/wakeup-service/venv
    ```

4. Install the dependencies from [`requirements.txt`](requirements.txt)

    ```bash
    /usr/local/lib/wakeup-service/venv/bin/pip install -r requirements.txt
    ```

5. Install the wakeup service

    ```bash
    sudo cp wakeup.service /etc/systemd/system/
    sudo systemctl enable wakeup.service
    sudo systemctl start wakeup.service
    ```
