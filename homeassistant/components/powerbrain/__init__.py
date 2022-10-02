"""The cFos Powerbrain integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .powerbrain import Powerbrain

_LOGGER = logging.getLogger(__name__)

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

    # Create the updatecoordinator instance
    coordinator = PowerbrainUpdateCoordinator(
        hass, brain, entry.data[CONF_SCAN_INTERVAL]
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id + "_coordinator"] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class PowerbrainUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from the powerbrain api."""

    def __init__(self, hass, brain: Powerbrain, update_interval: int):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Powerbrain Api data",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=update_interval),
        )
        self.brain = brain

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            await self.hass.async_add_executor_job(self.brain.update_device_status)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
