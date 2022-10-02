"""Sensor platform."""

from datetime import timedelta
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .powerbrain import Device, Powerbrain

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Config entry example."""
    # assuming API object stored here by __init__.py
    brain: Powerbrain = hass.data[DOMAIN][entry.entry_id]

    coordinator = PowerbrainUpdateCoordinator(hass, brain)

    await coordinator.async_config_entry_first_refresh()

    entities = []
    for device in brain.devices.values():
        if not device.attributes["is_evse"]:
            entities.extend(create_meter_entities(coordinator, device))

    async_add_entities(entities)


class PowerbrainUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from the powerbrain api."""

    def __init__(self, hass, brain: Powerbrain):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Powerbrain Api data",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=20),
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


class PowerbrainDeviceSensor(CoordinatorEntity, SensorEntity):
    """Powerbrain device sensors."""

    def __init__(
        self,
        coordinator: PowerbrainUpdateCoordinator,
        device: Device,
        attr: str,
        name: str,
        unit: str,
        deviceclass: str = "",
        stateclass: str = SensorStateClass.MEASUREMENT,
    ) -> None:
        """Initialize sensor attributes."""
        super().__init__(coordinator)
        self.device = device
        self.attribute = attr
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.brain.attributes['vsn']['serialno']}_{self.device.dev_id}_{name}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.device.attributes[self.attribute]
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Information of the parent device."""
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device.name)
            },
            "name": self.device.name,
            "manufacturer": "cFos",
            "model": self.device.attributes["model"],
        }

    # @property
    # def state(self):
    #     return self._attr_state


def create_meter_entities(coordinator: PowerbrainUpdateCoordinator, device: Device):
    """Create the entities for a powermeter device."""
    ret = []

    ret.append(
        PowerbrainDeviceSensor(
            coordinator, device, "power", "Power", "W", SensorDeviceClass.POWER
        )
    )
    ret.append(
        PowerbrainDeviceSensor(
            coordinator,
            device,
            "import",
            "Import",
            "Wh",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
        )
    )
    ret.append(
        PowerbrainDeviceSensor(
            coordinator,
            device,
            "export",
            "Export",
            "Wh",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
        )
    )

    return ret
