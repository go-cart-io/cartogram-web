# Cartogram Web Visualization Project

## Running [go-cart.io](https://go-cart.io) locally

We recommend using Docker for running this project. Please follow the instructions on [go-cart-io/carotgram-docker](https://github.com/go-cart-io/cartogram-docker) to get setup.

## Project overview

This project uses the cartogram generation algorithm written by Gastner et. al. in 2018 to create an interactive cartogram-generating website. The project consists of 4 main folders:

- `internal`: contains all pages of cartogram web (e.g., home, cartogram, contact, etc.), written in python;
- `frontend`: contains interactive features in a cartogram page, written using VueJs;
- `docs`: contains documents;
- `data`: contains data used to generate cartograms.


## Adding a map

To add a map to the website, please follow the Add Map Wizard guide at [here](docs/addmap/addmap.md).

## Updating the `cartogram` binary from [mgastner/cartogram-cpp](https://github.com/mgastner/cartogram-cpp)

To update the `cartogram` binary to:

- The latest available build on `cartogram-cpp`
    1. Run the following command:

  ```shell script
  bash tools/pull-executable.sh --latest
  ```

- A specific release from `cartogram-cpp`
    1. Update `/internal/executable/release-tag.txt` with the desired release tag.
       -  You may find the available releases [here](https://github.com/mgastner/cartogram-cpp/releases).
    2. Run the following command:

  ```shell script
  bash tools/pull-executable.sh
  ```
### Pushing changes to [go-cart.io](https://go-cart.io)

To push changes to production (for instance, adding a map, updating the `cartogram` binary, or any other changes), please follow the the instructions on [go-cart-io/carotgram-docker](https://github.com/go-cart-io/cartogram-docker).

# Contact

If you encounter issues using this code, or have any questions, please contact Atima at atima.tharatipyakul@singaporetech.edu.sg.
