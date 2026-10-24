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

from innosonix import InnosonixApiException

from .coordinator import InnosonixCoordinator
from .const import DATA_COORDINATOR, DOMAIN
from .entity import InnosonixChannelEntity

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


class InnosonixChannelSwitch(InnosonixChannelEntity, SwitchEntity):
    """Per-channel amplifier enable / mute switch."""

    def __init__(
        self,
        coordinator: InnosonixCoordinator,
        channel_id: int,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch.

        ``description.key`` is "amp" (amplifier enabled) or "mute" (muted).
        """
        super().__init__(coordinator)
        self.entity_description = description
        self.channel_id = channel_id
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-ch{channel_id}-{description.key}"
        )

    @property
    def is_on(self) -> bool:
        """Return True when the amp is enabled / channel is muted."""
        channel = self._channel
        return channel.amp_enabled if self.entity_description.key == "amp" else channel.muted

    @property
    def icon(self) -> str:
        """Return an icon reflecting the switch's current state."""
        if self.entity_description.key == "amp":
            return "mdi:volume-high" if self.is_on else "mdi:volume-variant-off"
        return "mdi:volume-mute" if self.is_on else "mdi:volume-high"

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
                    self.channel_id, value
                )
            else:
                await self.coordinator.client.set_channel_muted(
                    self.channel_id, value
                )
        except (InnosonixApiException, aiohttp.ClientError, OSError) as err:
            raise HomeAssistantError(
                f"Failed to set {self.entity_description.key} on channel "
                f"{self.channel_id}: {err}"
            ) from err
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Innosonix switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [
        InnosonixChannelSwitch(coordinator, channel.channel_id, description)
        for channel in coordinator.data.channels
        for description in SWITCH_TYPES
    ]
    async_add_entities(entities)
