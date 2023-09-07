# Cartogram Web Visualization Project

This project uses the cartogram generation algorithm written by Gastner et. al. in 2018 to create an interactive cartogram-generating website. The project consists of 4 main folders:

- `internal` contains all pages of cartogram web (e.g., home, cartogram, contact, etc.), written in python;
- `frontend` contains interactive features in a cartogram page, written using VueJs;
- `doc` contains documents;
- `data` contains data used to generate cartograms.

## Installation

We recommend using docker to get project running on your computer. You can follow the instruction on https://github.com/jansky/cartogram-docker but use this repository when cloning cartogram-web.

```shell script
git clone https://github.com/atima/cartogram-web.git
```

You should change `DEBUG` variable in `cartogram-web/internal/settings.py` to `False` before starting the docker. Then you can access the locally-running website at http://localhost:5000.

## Development

### Frontend

You need to install [Node.js](https://nodejs.org), then run the following commands to start development server:

```shell script
# After install Nodejs
cd part-to-cartogram-web/frontend
npm install
npm run dev
```

Make sure that `DEBUG` variable in `cartogram-web/internal/settings.py` is set to `True`.

Once you finish modifying the code, you must build the project and change `DEBUG` variable to `False` so the changes reflect in the production server.

```shell script
npm run build
```

Now you should found updated frontend code in `internal/static/dist`.

### Internal

To get the python website running locally on your computer, please follow the Linux or Mac OS X setup guide in the `doc/` folder in this repository. To add a map to the website, please follow the Add Map Wizard guide at `doc/addmap/addmap.md`.

Alternatively, you can use docker so you can make small changes without the need to setup python development environment. The following commands could be useful:

- `docker-compose up -d` to start docker containers in the background (so you can use command line for other thing);
- `docker exec -it cartogram-docker_web_1 /bin/bash` to access the cartogram-web container (so you can use python to run a file, such as `python addmap.py init test`);
- `docker start cartogram-docker_web_1` to start the cartogram-web container (which is useful when the container stops because of error in python code);
- `docker logs --follow cartogram-docker_web_1` to see the log in the cartogram-web container.

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

# Contact

If you encounter issues using this code, or have any questions, please contact Atima at atima.tharatipyakul@singaporetech.edu.sg.
