Insekta-web Installation Guide
==============================

Pre-Requirements
------------

The following debian packages are requiered:

`apt install git wget python3 python3-pip unzip gettext`


Install nodejs and npm
----------------------

`curl -sL https://deb.nodesource.com/setup_9.x | sudo -E bash -`

`sudo apt-get install -y nodejs`


Create pipenv
-------------

`pip3 install pipenv`


Create Configuration
--------------------

Copy the default configuration file and adjust the variables if needed.

`cp ./insekta/insekta/settings.py.example ./insekta/insekta/settings.py`


Prepare and run server
----------------------

First make sure, you run the following commands in the pipenv shell:
`pipenv shell`

Execute the Makefile:
`make all`

Run django migration:
`python3 manage.py migrate`

Run insekta-web server itself:
`python3 manage.py runserver`


Enjoy
-----

Your Insekta installation is now available on port 8000.

Have fun! :)
