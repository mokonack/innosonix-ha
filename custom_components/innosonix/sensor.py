"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Sensor platform for the Innosonix integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, VOLTAGE
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
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="serial_number",
        translation_key="serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="software_revision",
        translation_key="software_revision",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="channel_count",
        translation_key="channel_count",
    ),
    SensorEntityDescription(
        key="master_volume",
        translation_key="master_volume",
        native_unit_of_measurement="dB",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="psu_voltage",
        translation_key="psu_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="psu_load",
        translation_key="psu_load",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
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
    def native_value(self) -> str | int | float | None:
        """Return the current value."""
        device = self.coordinator.data.device
        key = self.entity_description.key
        if key == "channel_count":
            return len(self.coordinator.data.channels)
        if key == "model":
            return device.model_name
        if key == "serial_number":
            return device.serial
        if key == "software_revision":
            return device.sw_revision
        if key == "master_volume":
            return self.coordinator.data.master_volume
        if key == "psu_voltage":
            return self.coordinator.data.psu.voltage_v
        if key == "psu_load":
            return self.coordinator.data.psu.load_pct
        return None

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