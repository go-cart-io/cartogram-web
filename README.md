**⚠ Experimental Branch Notice**
This branch was used for experiments in the study "Effectiveness of Touch-Based View Adjustments for Contiguous Area Cartograms." It is preserved solely for reproducibility purposes. Not all features are functional—cartogram generation is disabled, and the contact form is non-operational. **This branch should not be used in production.**

# Cartogram Web Visualization Project

This project uses the cartogram generation algorithm written by Gastner et. al. in 2018 to create an interactive cartogram-generating website. The project consists of 4 main folders:

- `internal` contains all pages of cartogram web (e.g., home, cartogram, contact, etc.), written in python;
- `frontend` contains interactive features in a cartogram page, written using VueJs;
- `doc` contains documents;
- `data` contains data used to generate cartograms.

## Installation

1. Install Docker and Docker Compose using [Official installation guide](https://docs.docker.com/engine/install/)

   - Add your user to the docker group by using a terminal to run:

   ```shell script
   sudo usermod -aG docker $USER
   ```

   - Sign out and back in again so your changes take effect.

2. Clone repository and switch to `exp-stretch` branch:

   ```shell script
   git clone https://github.com/go-cart-io/cartogram-web.git cartogram-web-exp
   cd cartogram-web-exp
   git checkout exp-stretch
   ```

3. Run the following commands:

   ```shell script
   docker compose up -d
   ```

   The first time you run this command, it may take a while to download and install dependencies. Once everything stats up, you should be able to access the locally-running instance of go-cart.io website at [http://localhost:5003](http://localhost:5003).

4. When you would like to stop the go-cart.io local instance, use the command:

   ```shell script
   docker compose stop
   ```

## Tablet testing via local network

First, you must allow other devices to access docker. If you use wsl on Windows, you can run the following command in command prompt (may need to run as administrator):

```shell script
netsh advfirewall firewall add rule name="Allowing LAN connections" dir=in action=allow protocol=TCP localport=5000

bash.exe -c "ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'"

netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=5000 connectaddress=<your-docker-ip> connectport=5000
```

Reference: https://stackoverflow.com/questions/61002681/connecting-to-wsl2-server-via-local-network

If you are running the application in development mode, you should allow other computher to access port 5173 (for Windows, you can see https://www.devopinion.com/access-localhost-from-another-computer-on-the-same-network/). If you cannot access 5173, check firewall, e.g., delete rules that block node.js.

You should be able to access the application using `http:\\your-local-ip:5000`

## Tablet testing via USB (Andriod)

Please follow this tutorial https://developer.chrome.com/docs/devtools/remote-debugging/. Then, setup port forwarding for port 5000 and 5173, see https://developer.chrome.com/docs/devtools/remote-debugging/local-server/.
