"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Number platform for the Innosonix integration."""

from __future__ import annotations

import aiohttp

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from innosonix import InnosonixApiException

from .coordinator import InnosonixCoordinator, get_device_info
from .const import DATA_COORDINATOR, DOMAIN

# Channel volume range in dB, per the Innosonix REST API (NumberOptions).
VOLUME_MIN = -72.0
VOLUME_MAX = 24.0
VOLUME_STEP = 0.1


class InnosonixChannelVolume(
    CoordinatorEntity[InnosonixCoordinator], NumberEntity
):
    """Per-channel volume number entity (dB)."""

    _attr_has_entity_name = True
    _attr_native_min_value = VOLUME_MIN
    _attr_native_max_value = VOLUME_MAX
    _attr_native_step = VOLUME_STEP
    _attr_native_unit_of_measurement = "dB"

    def __init__(
        self,
        coordinator: InnosonixCoordinator,
        channel_id: int,
        name: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._channel_id = channel_id
        self._attr_name = f"{name} volume"
        self._attr_translation_key = "volume"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-ch{channel_id}-volume"

    @property
    def _channel(self):
        """Return the channel data for this entity."""
        return next(
            channel
            for channel in self.coordinator.data.channels
            if channel.channel_id == self._channel_id
        )

    @property
    def native_value(self) -> float:
        """Return the current volume in dB."""
        return self._channel.volume

    async def async_set_native_value(self, value: float) -> None:
        """Set the channel volume on the device and refresh the coordinator."""
        try:
            await self.coordinator.client.set_channel_volume(
                self._channel_id, float(value)
            )
        except (InnosonixApiException, OSError, aiohttp.ClientError) as err:
            raise HomeAssistantError(
                f"Failed to set volume on channel {self._channel_id}: {err}"
            ) from err
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> dict:
        """Return device information."""
        return get_device_info(self.coordinator)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Innosonix number entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        InnosonixChannelVolume(coordinator, channel.channel_id, channel.name)
        for channel in coordinator.data.channels
    )
