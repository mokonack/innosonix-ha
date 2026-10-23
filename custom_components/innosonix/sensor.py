"""Sensor platform for the Innosonix integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import InnosonixCoordinator, get_device_info
from .const import DATA_COORDINATOR, DOMAIN

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="model",
        translation_key="model",
        device_class=SensorDeviceClass.MODEL,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="serial_number",
        translation_key="serial_number",
        device_class=SensorDeviceClass.SERIAL_NUMBER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="software_revision",
        translation_key="software_revision",
        device_class=SensorDeviceClass.SOFTWARE_VERSION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="channel_count",
        translation_key="channel_count",
    ),
)


class InnosonixSensor(CoordinatorEntity[InnosonixCoordinator], SensorEntity):
    """Sensor entity backed by the Innosonix data coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InnosonixCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-{description.key}"
        )

    @property
    def native_value(self) -> str | int | None:
        """Return the current value."""
        data = self.coordinator.data
        if self.entity_description.key == "channel_count":
            return len(data.channels)
        return getattr(data.device, self.entity_description.key, None)

    @property
    def device_info(self) -> dict:
        """Return device information."""
        return get_device_info(self.coordinator)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Innosonix sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        InnosonixSensor(coordinator, description) for description in SENSOR_TYPES
    )