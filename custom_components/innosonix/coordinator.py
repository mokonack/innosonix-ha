"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Data update coordinator for the Innosonix integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from innosonix import (
    DeviceInfo,
    InnosonixApiClient,
    InnosonixApiException,
    InnosonixChannel,
)
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class InnosonixData:
    """Snapshot of all data polled from the amplifier."""

    device: DeviceInfo
    channels: list[InnosonixChannel]


class InnosonixCoordinator(DataUpdateCoordinator[InnosonixData]):
    """Coordinator that polls the Innosonix REST API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry: ConfigEntry,
        client: InnosonixApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
        )
        self._client = client

    async def _async_update_data(self) -> InnosonixData:
        """Fetch device info and channels from the amplifier."""
        try:
            device = await self._client.get_device_infos()
            channels = await self._client.get_channels()
        except InnosonixApiException as err:
            raise UpdateFailed(f"Error communicating with Innosonix API: {err}") from err
        except (aiohttp.ClientError, OSError) as err:
            raise UpdateFailed(f"Error communicating with Innosonix API: {err}") from err

        return InnosonixData(device=device, channels=channels)


def get_device_info(coordinator: InnosonixCoordinator) -> dict:
    """Return the device info dict for entities."""
    device = coordinator.data.device
    entry = coordinator.config_entry
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": "Innosonix",
        "manufacturer": "Innosonix",
        "model": device.model_name,
        "sw_version": device.sw_revision,
        "serial_number": device.serial,
    }
