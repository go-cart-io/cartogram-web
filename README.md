# cartogram-web: Web-based Cartogram Generator

cartogram-web is a web-based tool designed to simplify the creation of contiguous cartograms. It provides a user-friendly, browser-based interface that makes cartogram creation accessible to a wider audience. You can use the tool online at https://go-cart.io.

This repository contains the source code behind the go-cart.io website. Users can input data through a streamlined interface, while a remote server performs fast flow-based cartogram calculations using a binary from [mgastner/cartogram-cpp](https://github.com/mgastner/cartogram-cpp).

We recommend using [go-cart.io](https://go-cart.io) for cartogram generation. However, if you want to run the tool locally, we suggest using [go-cart-io/carotgram-docker](https://github.com/go-cart-io/cartogram-docker). To push changes to go-cart.io (for instance, adding a map, updating the `cartogram` binary, or any other changes), please follow the the instructions [here](https://github.com/go-cart-io/cartogram-docker/blob/main/docs/deploy.md).

## Repository overview

This repository consists of three main folders:

- `internal`: Contains all pages of the site (e.g., home, cartogram, contact, etc.), written in Python.
- `frontend`: Contains interactive features of the site, written using Vue.js.
- `tools`: Contains utility tools that are not part of the site.

## Updating the `cartogram` binary from [mgastner/cartogram-cpp](https://github.com/mgastner/cartogram-cpp)

To update the `cartogram` binary to:

- The latest available build on `cartogram-cpp`

  1. Run the following command:

  ```shell script
  bash tools/pull-executable.sh --latest
  ```

- A specific release from `cartogram-cpp`

  1. Update `/internal/executable/release-tag.txt` with the desired release tag.
     - You may find the available releases [here](https://github.com/mgastner/cartogram-cpp/releases).
  2. Run the following command:

  ```shell script
  bash tools/pull-executable.sh
  ```

# Contributing

Contributions are highly encouraged, and we love pull requests! Feel free to take a stab at any of the open issues. If there are no issues, don't hesitate to suggest new features, or report bugs under the issues tab (and, optionally, even subsequently send in pull requests with said enhancements or fixes). If you need help getting setup or more guidance contributing, please @ any of the main contributors under the issue you'd like to help solve, and we'll be happy to guide you!
