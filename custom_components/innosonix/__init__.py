"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

The Innosonix Amplifier integration for Home Assistant."""

from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from innosonix import InnosonixApiClient

from .const import (
    CONF_API_KEY,
    CONF_HOST,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_SESSION,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import InnosonixCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Innosonix from a config entry."""
    session = aiohttp.ClientSession()
    client = InnosonixApiClient(
        entry.data[CONF_HOST],
        entry.data.get(CONF_API_KEY) or None,
        session=session,
    )
    coordinator = InnosonixCoordinator(hass, entry=entry, client=client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_SESSION: session,
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.forward_entry_setups(PLATFORMS, entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    data = hass.data[DOMAIN].pop(entry.entry_id)
    await data[DATA_SESSION].close()
    return True