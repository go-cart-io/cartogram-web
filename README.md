# Cartogram Web Visualization Project

This project uses the cartogram generation algorithm written by Gastner et. al. in 2018 to create an interactive cartogram-generating website. The project consists of 4 main folders:

- `internal` contains all pages of cartogram web (e.g., home, cartogram, contact, etc.), written in python;
- `frontend` contains interactive features in a cartogram page, written using VueJs;
- `docs` contains documents;
- `data` contains data used to generate cartograms.

We recommend Docker for running this project. See https://github.com/go-cart-io/cartogram-docker.

For local development, and updating the docker image, please run

```shell script
bash tools/pull-executable.sh
```

before following the [Linux](docs/setup-linux.md) or [macOS](docs/setup-macos.md) setup guide to get your local python environment up and running. Please note that the guide may not up-to-date, so reach out to a team member if you can!

To update the cartogram-cpp binary, use the `--latest` flag with the previous command like so:

```shell script
bash tools/pull-executable.sh --latest
```

Then, get your development environment up and running like before, and make sure you test everything thoroughly before submitting a pull request to main. Once your pull request is approved, a new image will automatically be created and pushed to docker hub with the release-tag specified in `/internal/executable/release-tag.txt`. When you run `bash tools/pull-executable.sh --latest`, this file will be automatically updated.

To add a map to the website, please follow the Add Map Wizard guide at [here](docs/addmap/addmap.md).

# Contact

If you encounter issues using this code, or have any questions, please contact Atima at atima.tharatipyakul@singaporetech.edu.sg.
