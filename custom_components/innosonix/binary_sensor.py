"""Binary sensor platform for the Innosonix integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import InnosonixCoordinator, get_device_info
from .const import DATA_COORDINATOR, DOMAIN

DEVICE_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="device_error",
        translation_key="device_error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="device_warning",
        translation_key="device_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


class InnosonixDeviceBinarySensor(
    CoordinatorEntity[InnosonixCoordinator], BinarySensorEntity
):
    """Device-level problem binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InnosonixCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-{description.key}"
        )

    @property
    def is_on(self) -> bool:
        """Return True when the problem flag is set."""
        device = self.coordinator.data.device
        if self.entity_description.key == "device_error":
            return device.error
        return device.warning

    @property
    def device_info(self) -> dict:
        """Return device information."""
        return get_device_info(self.coordinator)


class InnosonixChannelBinarySensor(
    CoordinatorEntity[InnosonixCoordinator], BinarySensorEntity
):
    """Per-channel amplifier enable / mute binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InnosonixCoordinator,
        channel_id: int,
        name: str,
        kind: str,
    ) -> None:
        """Initialize the binary sensor.

        kind is "amp" (amplifier enabled) or "mute" (channel muted).
        """
        super().__init__(coordinator)
        self._channel_id = channel_id
        self._kind = kind
        self._attr_name = name if kind == "amp" else f"{name} muted"
        self._attr_translation_key = kind
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-ch{channel_id}-{kind}"
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
        return channel.amp_enabled if self._kind == "amp" else channel.muted

    @property
    def device_info(self) -> dict:
        """Return device information."""
        return get_device_info(self.coordinator)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Innosonix binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = [
        InnosonixDeviceBinarySensor(coordinator, description)
        for description in DEVICE_SENSORS
    ]
    for channel in coordinator.data.channels:
        entities.append(
            InnosonixChannelBinarySensor(
                coordinator, channel.channel_id, channel.name, "amp"
            )
        )
        entities.append(
            InnosonixChannelBinarySensor(
                coordinator, channel.channel_id, channel.name, "mute"
            )
        )
    async_add_entities(entities)
