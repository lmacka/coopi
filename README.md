# A Raspberry Pi in a Chicken Coop

![Build Status](https://github.com/lmacka/coopi/actions/workflows/docker-build.yml/badge.svg)
![Pylint Status](https://github.com/lmacka/coopi/actions/workflows/pylint.yml/badge.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/lmacka/coopi)
![Docker Stars](https://img.shields.io/docker/stars/lmacka/coopi)
![Docker Image Size](https://img.shields.io/docker/image-size/lmacka/coopi/latest)
![Docker Build Status](https://img.shields.io/docker/cloud/build/lmacka/coopi)
![Docker Automated Build](https://img.shields.io/docker/automated/lmacka/coopi)
![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Dependencies](https://img.shields.io/librariesio/github/lmacka/coopi)


This is a simple door controller running on a Pi Zero to allow ad-hoc and scheduling of coop door operation.

![The Exodus](static/img/the_exodus.gif)


# Requirements
 - [Raspberry Pi Zero](https://core-electronics.com.au/raspberry-pi-zero-w-wireless.html)
 - Generic 12V power supply
 - [12v to 5v step down converter](https://core-electronics.com.au/buck-converter-6-20v-to-5v-3a.html)
 - 12v linear actuator with built in end stops (cheap on eBay)
 - [2 channel relay board](https://core-electronics.com.au/5v-2-channel-relay-module-10a.html)
 - An old plastic box
 - A coop with chickens


![Circuit design](static/img/sketch.png)

<p align="center">
  <a href="static/img/door.jpg"><img src="static/img/door.jpg" alt="Finished installation" width="45%"/></a>
  <a href="static/img/controller.jpg"><img src="static/img/controller.jpg" alt="Controller" width="45%"/></a>
</p>




## Quickstart
To get started with the door controller software, follow these steps:

1. Install the necessary dependencies. You can do this by running the following command:

    ```bash
    sudo apt-get install nginx python3-flask python3-rpi.gpio
    ```

2. Next, navigate to the `extras/` directory. You may need to modify these files to suit your environment.

3. Copy the system configuration files to the appropriate locations. For example, you can use the following commands to copy the files:

    ```bash
    sudo cp extras/nginx.conf /etc/nginx/sites-enabled/default
    sudo cp extras/config.service /etc/systemd/system/coopi.service
    sudo systemctl daemon-reload
    ```

    Make sure to replace `/home/pi/coopi` with the actual path to your project's directory.

4. Once the files are copied, open the `config.py` file and configure it according to your needs. This file contains various settings for the door controller, such as actuator cycle time and GPIO pin assignments.

5. After configuring `config.py`, restart nginx to apply the changes:

    ```bash
    sudo systemctl enable nginx
    sudo systemctl start nginx
    sudo systemctl enable coopi
    sudo systemctl start coopi
    ```
6. Browse to http://your-ip to access the door controller web UI.

<p align="center">
  <img src="static/img/screenshot.png" alt="UI" style="width: 350px;"/>
</p>