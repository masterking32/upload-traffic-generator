import asyncio
import io
import json
import logging
import random
import subprocess
import time
import uuid

import psutil
import pycurl
import requests

# Configure logging
LOG_LEVEL = logging.INFO
logging.basicConfig(
        level=LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


# Define upload speed thresholds
DYNAMIC_SPEED = 50 # if thats false, Mean get upload speed from speed test, If You put something like 100 that mean 100Mbps
RATE_UPLOAD = 15 # Upload until total server upload is 11x more than Download.

NETWORK_ADAPTER = "ens3" # Your network adapter name

async def run_speed_test():
    cmd = "speedtest-cli --json --no-download"
    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()
        result = json.loads(stdout)
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from speedtest-cli: {e}")
        return None
    except asyncio.TimeoutError:
        logger.error("Timeout occurred while running speed test.")
        return None

def get_speed_test_servers_data():
    links = [
        # 'https://www.speedtest.net/api/js/servers?engine=js&limit=20&https_functional=true',
        'https://www.speedtest.net/api/js/servers?engine=js&search=MCI&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Irancell&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Tehran&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Tabriz&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Ahvaz&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Esfahan&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Isfahan&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Shiraz&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Mashhad&https_functional=true&limit=100',
        'https://www.speedtest.net/api/js/servers?engine=js&search=Hamedan&https_functional=true&limit=100',
    ]

    unique_servers = {}

    for link in links:
        try:
            response = requests.get(link)
            servers = response.json()

            if not isinstance(servers, list):
                raise ValueError('Invalid server data. Servers property is missing or not an array.')

            for server in servers:
                id = server['id']
                server_key = id.lower()

                if server_key in unique_servers:
                    continue

                new_server = {
                    'url': server['url'],
                    'lat': server['lat'],
                    'lon': server['lon'],
                    'name': f"{server['country']} - {server['sponsor']} - {server['name']}",
                    'country': server['country'],
                    'cc': server['cc'],
                    'sponsor': server['sponsor'],
                    'id': id,
                    'preferred': 0,
                    'https_functional': server['https_functional'],
                    'host': server.get('host', ''),
                }

                unique_servers[server_key] = new_server

        except Exception as error:
            logger.debug(f"Error retrieving server data: {error}")

    return list(unique_servers.values())

async def get_network_stats(network_adapter):
    stats1 = psutil.net_io_counters(pernic=True)[network_adapter]
    await asyncio.sleep(1)
    stats2 = psutil.net_io_counters(pernic=True)[network_adapter]

    incoming_bps = stats2.bytes_recv - stats1.bytes_recv
    outgoing_bps = stats2.bytes_sent - stats1.bytes_sent

    incoming_mbps = (incoming_bps / (1024 * 1024))
    outgoing_mbps = (outgoing_bps / (1024 * 1024))
    download_mbps = (stats2.bytes_recv / (1024 * 1024))
    upload_mbps = (stats2.bytes_sent / (1024 * 1024))

    return incoming_mbps, outgoing_mbps, download_mbps, upload_mbps

async def close_app(sleepTime):
    await asyncio.sleep(sleepTime)
    return

def upload_callback(buf, size, nmemb):
    # Read data from the BytesIO object
    data = io_chunk.read(size * nmemb)
    return data

io_chunk = io.BytesIO(b"\x00" * 1024 * 1024 * 1024)
def upload_with_speed_limit(url, upload_speed_mbps):
    global io_chunk
    random_uid = str(uuid.uuid4())
    upload_url = f"{url}?nocache={random_uid}&guid="

    c = pycurl.Curl()
    c.setopt(pycurl.URL, upload_url)
    c.setopt(pycurl.POST, 1)

    upload_speed = int((upload_speed_mbps * 1024 * 1024) / 8)
    c.setopt(pycurl.MAX_SEND_SPEED_LARGE, upload_speed)

    # Set headers
    c.setopt(pycurl.HTTPHEADER, ['referer: https://www.speedtest.net/',
                                 'content-type: application/octet-stream'])

    # Use a BytesIO object to act as the "file" for each chunk
    c.setopt(pycurl.TIMEOUT, int(60))
    io_chunk = io.BytesIO(b"\x00" * 1024 * 1024 * 1024)
    c.setopt(pycurl.READDATA, io_chunk)
    # Perform the request
    try:
        c.perform()
    except pycurl.error as e:
        # logger.error(f"Error during upload: {e}")
        return
    finally:
        c.close()

UPLOAD_COUNTER = 0

async def main():
    global UPLOAD_COUNTER
    dynamic_speed = DYNAMIC_SPEED
    start_time = time.time()

    logger.info("Runing speed test...")
    result = await run_speed_test()
    if result is None or 'upload' not in result:
        logger.critical("Unable to get upload speed.")
    elif int(result['upload'] / 1000000) > dynamic_speed:
        dynamic_speed = int(result['upload'] / 1000000)

    upload_mbps = dynamic_speed
    logger.info("Total Upload Speed: {} Mbps".format(upload_mbps))

    logger.info("Getting SpeedTest server data for Iran...")
    speed_test_servers = get_speed_test_servers_data()

    if not speed_test_servers or len(speed_test_servers) == 0:
        logger.critical("No SpeedTest servers available.")
        logger.critical("Application will close in 10 minutes...")
        return await close_app(600)
    
    logger.info("Starting ...")
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= 36000:  # 10 hours in seconds
            logger.info("Program has run for 10 hours. Exiting...")
            return await close_app(30)

        download_speed, upload_speed, downloads, uploads = await get_network_stats(NETWORK_ADAPTER)
        if uploads > downloads * RATE_UPLOAD:
            logger.info("Uploads is more than download, so that's fine.")
            await asyncio.sleep(60)
            continue

        upload_percent = int(upload_mbps * 0.80)
        if upload_percent < upload_speed:
            logger.info("80% of server upload is full!")
            await asyncio.sleep(60)
            continue
        
        random_server = random.choice(speed_test_servers)
        speed_to_upload = (upload_percent - upload_speed) / 1.5
        if int(speed_to_upload) < 5:
            logger.info("Upload speed is low!")
            await asyncio.sleep(60)
            continue

        logger.info(f'Uploading on {random_server["name"]} with speed {speed_to_upload}')
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, upload_with_speed_limit, f"{random_server['url']}", int(speed_to_upload))
        await asyncio.sleep(1)

        UPLOAD_COUNTER += 1
        if UPLOAD_COUNTER % 10 == 0:
            sleep_time = random.randint(60, 300)
            logger.info(f"Completed 10 uploads. Waiting for {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)
            UPLOAD_COUNTER = 0


if __name__ == "__main__":
    asyncio.run(main())
