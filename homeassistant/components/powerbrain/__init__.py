"""The cFos Powerbrain integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .powerbrain import Powerbrain

# List the platforms that you want to support.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up cFos Powerbrain from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    # Create Api instance
    brain = Powerbrain(entry.data[CONF_HOST])

    # Validate the API connection (and authentication)
    try:
        await hass.async_add_executor_job(brain.get_params)
    except Exception as exc:
        raise ConfigEntryNotReady("Timeout while connecting to Powerbrain") from exc

    # Store an API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = brain

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
