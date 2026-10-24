# Innosonix Amplifier integration for Home Assistant

[![My Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=innosonix)
[![PyPI](https://img.shields.io/pypi/v/innosonix)](https://pypi.org/project/innosonix/)

A Home Assistant integration that reads status information from Innosonix
amplifiers (MAXX series) over the built-in REST API, built on top of the
standalone [`innosonix`](https://pypi.org/project/innosonix/) Python client
library published on PyPI.

## Features

- Device info sensors: model, serial number, software revision, channel count
- Device sensors: master volume, PSU voltage, PSU load
- Device health: error / warning problem binary sensors
- Per-channel switches: amplifier enable and mute (all channels)
- Per-channel volume: number entity in dB (all channels)
- Configurable API key (defaults to the key shipped with the amplifier)
- Local polling, no cloud required

## The Python client library

The `innosonix` package (`src/innosonix`) is a standalone async client for the
Innosonix REST API and works independently of Home Assistant:

```bash
pip install innosonix
```

```python
import asyncio
import aiohttp
from innosonix import InnosonixApiClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = InnosonixApiClient("192.168.1.50", session=session)
        device = await client.get_device_infos()
        print(device.model_name, device.sw_revision)
        print("master volume (dB):", await client.get_master_volume())
        print("psu:", await client.get_psu_status())
        channels = await client.get_channels()
        for ch in channels:
            print(ch.channel_id, ch.name, ch.amp_enabled, ch.muted, ch.volume)
        await client.set_channel_muted(1, True)
        await client.set_channel_volume(1, -6.0)

asyncio.run(main())
```

The Home Assistant integration lists the library as a requirement, so Home
Assistant installs it from PyPI automatically during setup.

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

## Releasing

This repository ships two artifacts that are released **independently**:

- **The Home Assistant integration** (`custom_components/innosonix`) — versioned
  in `manifest.json`, distributed via HACS.
- **The `innosonix` client library** (`src/innosonix`) — versioned in
  `pyproject.toml`, distributed on PyPI.

The only link between them is the integration's `requirements`, which must
point at an `innosonix` version that is already published on PyPI.

### Releasing the integration

1. On `main`, bump `version` in `custom_components/innosonix/manifest.json`
   (e.g. `0.3.0` → `0.3.1`). If the change relies on a new library feature,
   also bump `requirements` to that published `innosonix` version.
2. Create a GitHub **Release** tagged `vX.Y.Z` matching the manifest version.
   HACS users are then offered the update. This does **not** publish to PyPI.

### Releasing the library

1. On `main`, make the client changes and bump `version` in `pyproject.toml`.
2. Push a tag: `git tag lib-vX.Y.Z && git push origin lib-vX.Y.Z`.
   The *Publish to PyPI* workflow runs on `lib-v*` tags and publishes the
   library.

When an integration release depends on a newly released library, point its
`requirements` at that `innosonix` version before cutting the `v*` release.