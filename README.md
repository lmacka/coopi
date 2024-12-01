# A Pi-Powered Coop Door Controller <img src="coopi/static/favicon.png" alt="favicon" style="height: 1em; vertical-align: middle;">

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Version](https://img.shields.io/github/v/release/lmacka/coopi)
![Dependencies](https://img.shields.io/librariesio/github/lmacka/coopi)
![Pylint Status](https://github.com/lmacka/coopi/actions/workflows/pylint.yml/badge.svg)
![Security Scan](https://github.com/lmacka/coopi/actions/workflows/security-scan.yml/badge.svg)
![GHCR Build Status](https://github.com/lmacka/coopi/actions/workflows/docker-build.yml/badge.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/lmacka/coopi)
![Docker Stars](https://img.shields.io/docker/stars/lmacka/coopi)
![Docker Image Size](https://img.shields.io/docker/image-size/lmacka/coopi/latest)
![License](https://img.shields.io/github/license/lmacka/coopi)
![Last Commit](https://img.shields.io/github/last-commit/lmacka/coopi)
![Open Issues](https://img.shields.io/github/issues/lmacka/coopi)
![Code Size](https://img.shields.io/github/languages/code-size/lmacka/coopi)
![Platform](https://img.shields.io/badge/platform-raspberry%20pi-C51A4A)


This is a simple door controller running on a Pi Zero to allow ad-hoc operation and scheduling of a coop door.

![The Exodus](doc/img/the_exodus.gif)


# Requirements
 - [Raspberry Pi Zero](https://core-electronics.com.au/raspberry-pi-zero-w-wireless.html)
 - Generic 12V power supply
 - [12v to 5v step down converter](https://core-electronics.com.au/buck-converter-6-20v-to-5v-3a.html)
 - 12v linear actuator with built in end stops (cheap on eBay)
 - [2 channel relay board](https://core-electronics.com.au/5v-2-channel-relay-module-10a.html)
 - An old plastic box
 - A coop with chickens


![Circuit design](doc/img/sketch.png)

<p align="center">
  <a href="doc/img/door.jpg"><img src="doc/img/door.jpg" alt="Finished installation" width="45%"/></a>
  <a href="doc/img/controller.jpg"><img src="doc/img/controller.jpg" alt="Controller" width="45%"/></a>
</p>

<p align="center">
  <img src="doc/img/screenshot.png" alt="UI" style="width: 350px;"/>
</p>


## Quickstart
If you have built the unit as per the above instructions, you can simply install docker-compose and run
```bash
curl -s https://raw.githubusercontent.com/lmacka/coopi/main/docker-compose.yaml | docker-compose -f - up -d
```

So long as docker is set to start at boot, the application will come back after restarts.


