# Innosonix Amplifier integration for Home Assistant

[![My Home Assistant](https://my.home-assistant.io/badge.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=innosonix)

A custom integration for Home Assistant that reads status information from
Innosonix amplifiers (MAXX series) over the built-in REST API.

## Features

- Device info sensors: model, serial number, software revision, channel count
- Device health: error / warning problem binary sensors
- Per-channel binary sensors: amplifier enabled and mute state (all channels)
- Configurable API key (defaults to the key shipped with the amplifier)
- Local polling, no cloud required

## Installation

### HACS

1. Open HACS in Home Assistant.
2. Go to **Integrations** → **⋯** → **Custom Repositories**.
3. Add this repository's URL and choose the **Integration** category.
4. Find **Innosonix Amplifier** in HACS and install it.
5. Restart Home Assistant.

### Manual

Copy the `custom_components/innosonix` folder into the `custom_components`
folder of your Home Assistant configuration directory, then restart Home
Assistant.

## Setup

1. In Home Assistant, open **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Innosonix Amplifier**.
3. Enter the host name or IP address of your amplifier (e.g. `192.168.1.50`).
4. Optionally enter a custom API key.
5. Finish the flow.

## Requirements

- Home Assistant 2024.12 or newer