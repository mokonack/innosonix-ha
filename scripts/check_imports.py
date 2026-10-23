"""Import the integration and every platform module it declares.

Mirrors what the Home Assistant loader does at setup time, so module-level
import errors (missing files, bad imports, Home Assistant API drift) fail CI
instead of surfacing as a broken entry on the user's instance.

Requires `homeassistant` and the `innosonix` library to be installed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import custom_components.innosonix  # noqa: E402
from custom_components.innosonix import const  # noqa: E402

for platform in const.PLATFORMS:
    __import__(f"custom_components.innosonix.{platform.value}")
    print(f"imported custom_components.innosonix.{platform.value}")

print("All platform imports OK")
