"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Diagnostics support for the Innosonix integration."""

from __future__ import annotations

from dataclasses import asdict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_HOST, DATA_COORDINATOR, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    data = coordinator.data
    return {
        "config": {
            CONF_HOST: entry.data.get(CONF_HOST),
            CONF_API_KEY: "[redacted]" if entry.data.get(CONF_API_KEY) else None,
        },
        "device": asdict(data.device) if data else None,
        "channels": [asdict(channel) for channel in data.channels] if data else [],
    }
