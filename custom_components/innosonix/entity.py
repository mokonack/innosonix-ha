"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Shared base class for per-channel Innosonix entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from innosonix import InnosonixChannel

from .coordinator import InnosonixCoordinator
from .const import DOMAIN, MANUFACTURER


class InnosonixChannelEntity(CoordinatorEntity[InnosonixCoordinator]):
    """Base class for entities that belong to a channel sub-device.

    Each channel is registered as its own device linked to the amplifier
    device, so assigning a channel to a room moves all of its entities
    with it.
    """

    _attr_has_entity_name = True

    channel_id: int

    @property
    def _channel(self) -> InnosonixChannel:
        """Return the channel data for this entity."""
        return next(
            channel
            for channel in self.coordinator.data.channels
            if channel.channel_id == self.channel_id
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the channel sub-device information."""
        channel = self._channel
        info: DeviceInfo = {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self.coordinator.config_entry.entry_id}-ch{self.channel_id}",
                )
            },
            "name": channel.name or f"Channel {self.channel_id}",
            "manufacturer": MANUFACTURER,
        }
        if parent_id := self.coordinator.parent_device_id:
            info["via_device_id"] = parent_id
        return info
