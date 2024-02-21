For the moment this is just a few scripts. It may become a python3 version of the DAQ... Ideal the daq would be written in Rust or another safe langugage.

- Step 1, get and install python 3.10.13 ([this may help](https://raspberrytips.com/install-latest-python-raspberry-pi/))
  - `wget <python tarball>`
  - `tar -zxvf <tarball>`
  - `cd <Python-3.10>`
  - configure, making sure to enable ssl `./configure --enable-optimizations --with-openssl=/usr/include` (if you don't have openssl `which openssl` install it with `sudo apt-get install openssl libssl-dev`)
  - install it `sudo make altinstall`
- Step 2, make sure you have python 3.10.13 and use it to create a venv with virtualenv
  - install virtualenv `pip3.10 install virtualenv`
  - initiate a virtualenv somewhere reasonable `cd /some/reasonable/path` then `virtualenv <environment-name>`
  - activate the virtualenv `source <environment-name>/bin/acitivate`
- Step 3, install capser's python3.10 development branch 
  - clone the branch `git clone https://github.com/casper-astro/casperfpga`
  - install...
- Step 4, install requirements
- Step 5, run code...


