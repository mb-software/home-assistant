"""Switch platform of powerbrain integration."""

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .__init__ import PowerbrainUpdateCoordinator, get_entity_deviceinfo
from .const import DOMAIN
from .powerbrain import Evse, Powerbrain


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the switch entities for powerbrain integration."""
    brain: Powerbrain = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in brain.devices.values():
        if device.attributes["is_evse"]:
            entities.append(
                EvseSwitchEntity(
                    hass.data[DOMAIN][entry.entry_id + "_coordinator"],
                    device,
                    "Charging Enabled",
                )
            )
    async_add_entities(entities)


class EvseSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Switch entity for evse."""

    def __init__(
        self, coordinator: PowerbrainUpdateCoordinator, device: Evse, name: str
    ) -> None:
        """Initialize entity for charging current override."""
        super().__init__(coordinator)
        self.device = device
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.brain.attributes['vsn']['serialno']}_{self.device.dev_id}_{name}"
        self._attr_name = name
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_is_on = self.device.attributes["charging_enabled"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        await self.hass.async_add_executor_job(self.device.disable_charging, False)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn switch off."""
        await self.hass.async_add_executor_job(self.device.disable_charging, True)
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_is_on = self.device.attributes["charging_enabled"]
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Information of the parent device."""
        return get_entity_deviceinfo(self.device)
