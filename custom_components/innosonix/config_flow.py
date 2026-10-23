"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Config flow for the Innosonix integration."""

from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from innosonix import InnosonixApiClient, InnosonixApiException

from .const import CONF_API_KEY, CONF_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_API_KEY): str,
    }
)


async def validate_input(data: dict[str, str]) -> str:
    """Validate the host is reachable and return a display title."""
    session = aiohttp.ClientSession()
    try:
        client = InnosonixApiClient(data[CONF_HOST], data.get(CONF_API_KEY) or None, session=session)
        device = await client.get_device_infos()
    finally:
        await session.close()
    return device.hostname or data[CONF_HOST]


class InnosonixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Innosonix."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip().lower()
            if any(
                entry.data.get(CONF_HOST, "").strip().lower() == host
                for entry in self._async_current_entries()
            ):
                return self.async_abort(reason="already_configured")

            try:
                title = await validate_input(user_input)
            except (InnosonixApiException, aiohttp.ClientError, ValueError, OSError) as err:
                _LOGGER.debug("Failed to connect to %s: %s", user_input[CONF_HOST], err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )