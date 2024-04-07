# Network Upload Traffic Generator

This project is designed to generate simulated upload traffic for your server, based on your server's download activity. This is particularly useful for Iranian data centers, which require a 10x higher upload rate compared to the download rate to avoid bandwidth limitations. By using this project, you can circumvent this rule, as it creates simulated yet valid traffic using speedtest.net servers located within Iran.

### ❌ Please note: This project is currently in its beta stage and is intended for testing purposes only! ❌

### ⭐ If you find this project useful, please consider giving it a star! ⭐

# Installation on Ubuntu/Debian

Follow these steps to install the necessary software and packages:

1. Install software requirements:

```bash
apt update && apt install -y curl git nano python3 python3-pip net-tools sudo
```

2. Install [speedtest-cli](https://www.speedtest.net/apps/cli):

```bash
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt-get install speedtest
```

3. Install the required Python packages:

```bash
pip install psutil pycurl requests
```

or

```bash
pip install psutil pycurl requests --break-system-packages
```

4. Download the project:

```bash
git clone https://github.com/masterking32/upload-traffic-generator
cd upload-traffic-generator
```

6. Identify your network adapter name using the `ifconfig` command. Then, open `main.py` with an editor (like nano), find the NETWORK_ADAPTER line, and replace it with your network adapter name. For example: `NETWORK_ADAPTER = "eth0"`.

7. Run Project:

```bash
python3 ./main.py
```

## Running as a Linux Service

If you want to run this project as a service on Ubuntu, which will allow it to automatically start on boot and restart if it crashes, follow these steps:

1. Create a new service file:

```bash
sudo nano /etc/systemd/system/upload-traffic-generator.service
```

2. Add the following content to the file, replacing `/path/to/your/project` with the actual path to your project:

```
[Unit]
Description=Upload Traffic Generator
Documentation=https://masterking32.com
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/project/main.py
Restart=always
User=root
Environment=PATH=/usr/bin:/usr/local/bin
WorkingDirectory=/path/to/your/

[Install]
WantedBy=multi-user.target
```

3. Enable the service to start on boot:

```bash
sudo systemctl enable upload-traffic-generator
```

4. Start the service:

```bash
sudo systemctl start upload-traffic-generator
```

You can check the status of the service with:

```
sudo systemctl status upload-traffic-generator
```

---

Developed By [MasterkinG32](https://github.com/masterking32)
