"""SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Mokonack

Async Python client for the Innosonix MAXX / LP2 amplifier REST API.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, cast

import aiohttp

__version__ = "0.2.0"

__all__ = [
    "DEFAULT_API_KEY",
    "DeviceInfo",
    "InnosonixApiException",
    "InnosonixChannel",
    "InnosonixApiClient",
    "PsuStatus",
    "__version__",
]

DEFAULT_API_KEY = "f4005bf8507999192162d989d5a60823"


class InnosonixApiException(Exception):
    """The device returned an error status or an unexpected response."""

    def __init__(self, path: str, status_code: int, message: str) -> None:
        """Initialize the exception."""
        self.path = path
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error at {path}: {status_code} - {message}")


@dataclass(slots=True)
class DeviceInfo:
    """Device information as reported by GET /info/device."""

    model_name: str = ""
    hostname: str = ""
    serial: str = ""
    sw_revision: str = ""
    channel_count: int = 0
    error: bool = False
    warning: bool = False
    ok: bool = False
    options: list[str] = field(default_factory=list)
    mac: str = ""


@dataclass(slots=True)
class InnosonixChannel:
    """Channel settings as reported by GET /settings/channel."""

    channel_id: int
    name: str = ""
    amp_enabled: bool = False
    muted: bool = False
    volume: float = 0.0


@dataclass(slots=True)
class PsuStatus:
    """Power supply status as reported by GET /status/device/psu."""

    load_pct: int = 0
    voltage_v: float = 0.0
    reduction_db: float = 0.0
    fan_speed_pct: int = 0
    dc_ok: bool = True


def _value(payload: Any, default: Any = None) -> Any:
    """Unwrap the ``{"value": ...}`` envelope used by the API."""
    if isinstance(payload, dict) and "value" in payload:
        return payload["value"]
    return payload if payload is not None else default


class InnosonixApiClient:
    """Client for the Innosonix MAXX REST API (``http://<host>/rest-api``).

    Read-only endpoints do not require authentication; write operations send
    the API key as the ``token`` header.
    """

    def __init__(
        self,
        host: str,
        api_key: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the client.

        :param host: IP address, host name, or full base URL.
        :param api_key: API key for write operations (unused by reads).
        :param session: aiohttp session used for requests. The caller is
            responsible for closing it.
        """
        if not host or not host.strip():
            raise ValueError("host is required")
        if session is None:
            raise ValueError("a shared aiohttp.ClientSession is required")

        host = host.strip()
        if "://" not in host:
            host = f"http://{host}"
        self._base_url = f"{host.rstrip('/')}/rest-api/"
        self._api_key = api_key or DEFAULT_API_KEY
        self._session = session

    @property
    def base_url(self) -> str:
        """The full REST API base URL."""
        return self._base_url

    async def _get(self, path: str) -> Any:
        """GET ``path`` and return the decoded JSON body."""
        url = f"{self._base_url}{path.lstrip('/')}"
        async with self._session.get(url) as response:
            body = await response.text()
            if not response.ok:
                raise InnosonixApiException(path, response.status, body)
        try:
            return json.loads(body)
        except json.JSONDecodeError as err:
            raise InnosonixApiException(
                path, response.status, "response body could not be deserialized"
            ) from err

    async def get_device_infos(self) -> DeviceInfo:
        """Get information about the device (GET /info/device)."""
        data = cast(dict[str, Any], await self._get("info/device"))
        status = data.get("status_flags") or {}
        return DeviceInfo(
            model_name=data.get("model_name", ""),
            hostname=data.get("hostname", ""),
            serial=data.get("serial", ""),
            sw_revision=data.get("sw_revision", ""),
            channel_count=int(data.get("channel", 0)),
            error=bool(status.get("error", False)),
            warning=bool(status.get("warning", False)),
            ok=bool(status.get("ok", False)),
            options=list(data.get("options", [])),
            mac=data.get("mac", ""),
        )

    async def get_channels(self) -> list[InnosonixChannel]:
        """Get all channels of the device (GET /settings/channel)."""
        data = cast(list[dict[str, Any]], await self._get("settings/channel"))
        channels: list[InnosonixChannel] = []
        for item in data:
            dsp = item.get("dsp") or {}
            channels.append(
                InnosonixChannel(
                    channel_id=int(item.get("channel_id", 0)),
                    name=str(_value(item.get("name"), "")),
                    amp_enabled=bool(_value(item.get("ampenable"), False)),
                    muted=bool(_value(dsp.get("mute"), False)),
                    volume=float(_value(dsp.get("volume"), 0.0)),
                )
            )
        return channels

    async def _put(self, path: str, value: Any) -> None:
        """PUT ``{"value": ...}`` to ``path`` with the API key header."""
        url = f"{self._base_url}{path.lstrip('/')}"
        headers = {"token": self._api_key}
        async with self._session.put(url, json={"value": value}, headers=headers) as response:
            body = await response.text()
            if not response.ok:
                raise InnosonixApiException(path, response.status, body)

    async def get_master_volume(self) -> float:
        """Get the device master volume in dB (GET /settings/device/dsp/volume)."""
        data = await self._get("settings/device/dsp/volume")
        return float(_value(data, 0.0))

    async def get_psu_status(self) -> PsuStatus:
        """Get the power supply status (GET /status/device/psu)."""
        data = cast(dict[str, Any], await self._get("status/device/psu"))
        voltages = [float(v) for v in data.get("primary_voltage") or []]
        dc_ok = [bool(v) for v in data.get("dc_ok") or []]
        return PsuStatus(
            load_pct=int(data.get("load", 0)),
            voltage_v=voltages[0] if voltages else 0.0,
            reduction_db=float(data.get("reduction", 0.0)),
            fan_speed_pct=int(data.get("fan_speed", 0)),
            dc_ok=all(dc_ok) if dc_ok else True,
        )

    async def set_channel_amp_enabled(self, channel_id: int, enabled: bool) -> None:
        """Enable or disable the channel amplifier (PUT /settings/channel/{id}/ampenable)."""
        await self._put(f"settings/channel/{channel_id}/ampenable", enabled)

    async def set_channel_muted(self, channel_id: int, muted: bool) -> None:
        """Mute or unmute a channel (PUT /settings/channel/{id}/dsp/mute)."""
        await self._put(f"settings/channel/{channel_id}/dsp/mute", muted)

    async def set_channel_volume(self, channel_id: int, volume: float) -> None:
        """Set the channel volume in dB (PUT /settings/channel/{id}/dsp/volume)."""
        await self._put(f"settings/channel/{channel_id}/dsp/volume", volume)
