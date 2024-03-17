# Setting Up the Web Application on Mac OS X

This setup guide will help you get the go-cart web application up and running on Max OS X. This guide assumes that you already have Homebrew installed.

## Installing and Configuring Prerequisites

First, you need to install some third-party software dependencies. Open a new terminal window, and run the following command:

    $ brew install python3 postgresql

Now you'll need to install virtualenv, a tool that makes it easy to manage dependencies for Python projects:

    $ pip3 install virtualenv

Now you'll need to configure the PostgreSQL database server. PostgreSQL is a robust SQL database server go-cart uses to store users' generated cartograms so they can be shared on social media. In order for go-cart to use PostgreSQL, you'll need to first initialize it, then create an account and database:

    $ brew services start postgresql
    $ initdb /usr/local/var/postgres

If you receive the error

    initdb: directory "/usr/local/var/postgres" exists but is not empty
    If you want to create a new database system, either remove or empty
    the directory "/usr/local/var/postgres" or run initdb
    with an argument other than "/usr/local/var/postgres".

then run the following commands:

    $ rm -r /usr/local/var/postgres
    $ initdb /usr/local/var/postgres

Now you can create a PostgreSQL account and database for the web application:

    $ createuser --interactive --pwprompt gocart

Enter your chosen password when prompted, and answer no to all of the questions asked by typing `n` and pressing return each time:

    Enter password for new role: 
    Enter it again: 
    Shall the new role be a superuser? (y/n) n
    Shall the new role be allowed to create databases? (y/n) n
    Shall the new role be allowed to create more new roles? (y/n) n

Now, you can create the database:

    $ createdb -O gocart gocart

Now, you need to download and compile the cartogram generator. You must use the cartogram generator from the repository below, **not** the one from `Flow-Based-Cartograms/go_cart`.

    $ git clone https://github.com/mgastner/cartogram.git
    ...
    $ cd cartogram

Now you're ready to compile:

    $ chmod +x autobuild.sh
    $ ./autobuild.sh
    ...

Remember the path to the root of this repository, as you'll need it when configuring the web application later.

## Installing and Configuring the Web Application

First, clone the web application code from GitHub

    $ git clone https://github.com/jansky/cartogram-web

Now, you need to change some settings:

    $ cd cartogram-web/internal
    $ cp envsettings.sh.dist envsettings.sh
    $ open -a textedit envsettings.sh

In the third line, replace `/home/jansky/cartogram/cartogram_generator/cartogram` in `CARTOGRAM_EXE` with the path to the folder containing the cartogram generator, followed by `/cartogram_generator/cartogram`. For example, if the root of the cartogram generator repository is

    /home/jansky/cartogram

Then `CARTOGRAM_EXE` should be set to

    /home/jansky/cartogram/cartogram_generator/cartogram


In the fourth line, replace `/home/jansky/cartogram` in `CARTOGRAM_DATA_DIR` with the path to the folder containing the cartogram generator, followed by `/data`. Do not include a trailing slash.

For example, if the root of the cartogram generator repository is

    /home/jansky/cartogram

Then `CARTOGRAM_DATA_DIR` should be set to

    /home/jansky/cartogram/data


In the tenth line, in `CARTOGRAM_DATABASE_URI`, replace `username` with `gocart`, `password` with the database password you created, and `database` with `gocart`. Save the file and quit TextEdit.

Finally, you need to initialize the database:

    $ source ./setupenv.sh
    (venv) $ python3
    Python 3...
    ...
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import web
    >>> web.db.create_all()
    >>> exit()
    (venv) $

## Running the Web Application

When you want to run the web application, open a new terminal window and navigate to the root of the `cartogram-web` repository using `cd`. Then, run

    $ cd internal
    $ source ./setupenv.sh
    (venv) $ python web.py
    ...

Now, you can navigate to http://localhost:5000 in your web browser to access the go-cart web application. 

When you are finished, you can go back to the terminal window and press Control-C to kill the web application process.






