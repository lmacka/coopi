# A Pi-Powered Coop Door Controller <img src="coopi/static/favicon.png" alt="favicon" style="height: 1em; vertical-align: middle;">

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Version](https://img.shields.io/github/v/release/lmacka/coopi)
![Dependencies](https://img.shields.io/librariesio/github/lmacka/coopi)
![Pylint Status](https://github.com/lmacka/coopi/actions/workflows/pylint.yml/badge.svg)
![Security Scan](https://github.com/lmacka/coopi/actions/workflows/security-scan.yml/badge.svg)
![GHCR Build Status](https://github.com/lmacka/coopi/actions/workflows/docker-build.yml/badge.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/lmacka/coopi)
![Docker Image Size](https://img.shields.io/docker/image-size/lmacka/coopi/latest)
![Last Commit](https://img.shields.io/github/last-commit/lmacka/coopi)
![Code Size](https://img.shields.io/github/languages/code-size/lmacka/coopi)
![Platform](https://img.shields.io/badge/platform-raspberry%20pi-C51A4A)
[![balena Deploy](https://img.shields.io/badge/balena-deploy-blue)](https://dashboard.balena-cloud.com/deploy?repoUrl=https://github.com/lmacka/coopi)


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


## Getting Started

You've got two easy ways to get your chickens' automated door up and running:

### Option 1: Deploy with Balena (Recommended)
The easiest way to get started is using Balena. Just click the button below and follow the prompts:

[![balena Deploy Button](https://www.balena.io/deploy.svg)](https://dashboard.balena-cloud.com/deploy?repoUrl=https://github.com/lmacka/coopi)

This will:
1. Set up a Balena account if you don't have one
2. Create a new application for your coop door
3. Let you easily manage your device(s) through Balena's dashboard

### Option 2: Run with Docker
If you prefer the DIY approach, you can run it directly with Docker. Just make sure you have docker-compose installed and run:

```bash
curl -s https://raw.githubusercontent.com/lmacka/coopi/main/docker-compose.yaml | docker-compose -f - up -d
```

Both methods will automatically restart the application after power cycles or reboots, so your chooks won't get stuck!


