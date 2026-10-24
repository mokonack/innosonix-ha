"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Constants for the Innosonix integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "innosonix"
MANUFACTURER = "Innosonix"

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONF_HOST = "host"
CONF_API_KEY = "api_key"

DATA_CLIENT = "client"
DATA_SESSION = "session"
DATA_COORDINATOR = "coordinator"

SCAN_INTERVAL = timedelta(seconds=60)