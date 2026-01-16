from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import TapoAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    api: TapoAPI = entry_data["api"]

    coordinator = TapoCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    sensors_data = coordinator.data or {}
    _LOGGER.debug("Sensor setup: sensors data = %s", sensors_data)
    
    sensors = []
    
    if sensors_data:
        if "battery_percentage" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "battery_percentage",
                    "Battery",
                    "%",
                    SensorStateClass.MEASUREMENT,
                )
            )
        
        if "battery_low" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "battery_low",
                    "Battery Low",
                    None,
                    None,
                )
            )
        
        if "model" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "model",
                    "Model",
                    None,
                    None,
                )
            )
        
        if "firmware_version" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "firmware_version",
                    "Firmware Version",
                    None,
                    None,
                )
            )
        
        if "hardware_version" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "hardware_version",
                    "Hardware Version",
                    None,
                    None,
                )
            )
        
        if "nickname" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "nickname",
                    "Nickname",
                    None,
                    None,
                )
            )
        
        if "mac" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "mac",
                    "MAC Address",
                    None,
                    None,
                )
            )
        
        if "device_id" in sensors_data:
            sensors.append(
                TapoSensor(
                    coordinator,
                    entry.entry_id,
                    "device_id",
                    "Device ID",
                    None,
                    None,
                )
            )

    from .button import TapoButtonCoordinator, TapoButtonSensor
    button_coordinator = TapoButtonCoordinator(hass, api)
    await button_coordinator.async_config_entry_first_refresh()
    sensors.append(TapoButtonSensor(button_coordinator, entry.entry_id))

    _LOGGER.info("Setting up %d sensor entities", len(sensors))
    async_add_entities(sensors)


class TapoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: TapoAPI) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.api = api
        self._last_successful_update_time: datetime | None = None

    def get_last_successful_update_time(self) -> datetime | None:
        return self._last_successful_update_time

    async def _async_update_data(self) -> dict[str, Any]:
        _LOGGER.debug("Updating sensor coordinator data")
        try:
            sensor_data = await self.api.async_get_sensor_data()
            if sensor_data is None:
                _LOGGER.warning("Failed to get sensor data, returning empty dict")
                return {}
            _LOGGER.debug("Sensor data retrieved: %s", sensor_data)
            self._last_successful_update_time = datetime.now()
            return sensor_data
        except asyncio.TimeoutError as err:
            _LOGGER.warning("Timeout while getting sensor data: %s", err)
            return {}
        except Exception as err:
            _LOGGER.error("Unexpected error updating sensor coordinator: %s", err, exc_info=True)
            return {}


class TapoSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry_id: str,
        sensor_key: str,
        name: str,
        unit: str | None,
        state_class: SensorStateClass | None,
    ) -> None:
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._attr_name = f"Tapo {name}"
        self._attr_unique_id = f"{config_entry_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class

    @property
    def native_value(self) -> str | int | float | bool | None:
        if isinstance(self.coordinator.data, dict):
            value = self.coordinator.data.get(self._sensor_key)
            return value
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        
        if hasattr(self.coordinator, "get_last_successful_update_time"):
            last_update = self.coordinator.get_last_successful_update_time()
            attrs["last_successful_update"] = last_update.isoformat() if last_update else "Never"
        
        if hasattr(self.coordinator, "api") and hasattr(self.coordinator.api, "get_last_successful_auth_time"):
            last_auth = self.coordinator.api.get_last_successful_auth_time()
            attrs["last_successful_auth"] = last_auth.isoformat() if last_auth else "Never"
        
        return attrs

