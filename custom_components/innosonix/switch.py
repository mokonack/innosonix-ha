"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Switch platform for the Innosonix integration."""

from __future__ import annotations

import aiohttp

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from innosonix import InnosonixApiException

from .coordinator import InnosonixCoordinator, get_device_info
from .const import DATA_COORDINATOR, DOMAIN

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="amp",
        translation_key="amp",
    ),
    SwitchEntityDescription(
        key="mute",
        translation_key="mute",
    ),
)


class InnosonixChannelSwitch(
    CoordinatorEntity[InnosonixCoordinator], SwitchEntity
):
    """Per-channel amplifier enable / mute switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InnosonixCoordinator,
        channel_id: int,
        name: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch.

        ``description.key`` is "amp" (amplifier enabled) or "mute" (muted).
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._channel_id = channel_id
        self._attr_name = f"{name} amplifier" if description.key == "amp" else f"{name} mute"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-ch{channel_id}-{description.key}"
        )

    @property
    def _channel(self):
        """Return the channel data for this entity."""
        return next(
            channel
            for channel in self.coordinator.data.channels
            if channel.channel_id == self._channel_id
        )

    @property
    def is_on(self) -> bool:
        """Return True when the amp is enabled / channel is muted."""
        channel = self._channel
        return channel.amp_enabled if self.entity_description.key == "amp" else channel.muted

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable the amp / mute the channel."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable the amp / unmute the channel."""
        await self._async_set(False)

    async def _async_set(self, value: bool) -> None:
        """Write the state to the device and refresh the coordinator."""
        try:
            if self.entity_description.key == "amp":
                await self.coordinator.client.set_channel_amp_enabled(
                    self._channel_id, value
                )
            else:
                await self.coordinator.client.set_channel_muted(
                    self._channel_id, value
                )
        except (InnosonixApiException, aiohttp.ClientError, OSError) as err:
            raise HomeAssistantError(
                f"Failed to set {self.entity_description.key} on channel "
                f"{self._channel_id}: {err}"
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
    """Set up Innosonix switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [
        InnosonixChannelSwitch(
            coordinator, channel.channel_id, channel.name, description
        )
        for channel in coordinator.data.channels
        for description in SWITCH_TYPES
    ]
    async_add_entities(entities)
