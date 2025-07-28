"""Sensor platform for Alibaba Cloud."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ACCESS_KEY_ID
from .coordinator import AliyunDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: AliyunDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities_to_add = [
        TotalCostSensor(coordinator, entry),
        TotalTrafficSensor(coordinator, entry),
    ]
    
    # Dynamically add sensors for each service cost
    if coordinator.data:
        for service_code in coordinator.data.get("cost_by_service", {}):
            entities_to_add.append(ServiceCostSensor(coordinator, entry, service_code))

    async_add_entities(entities_to_add)        # 先注册实体
    await coordinator.async_request_refresh()  # 后刷新数据


class AliyunBillEntity(CoordinatorEntity, SensorEntity):
    """Base class for Alibaba Cloud sensors."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AliyunDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"Aliyun Bill ({self._config_entry.data[CONF_ACCESS_KEY_ID]})",
            manufacturer="Alibaba Cloud",
            model="BSS API",
            entry_type="service",
        )

    @property
    def available(self) -> bool:
        return True


class TotalCostSensor(AliyunBillEntity):
    """Sensor for total monthly cost."""

    _attr_name = "Current Month Total Cost"
    _attr_native_unit_of_measurement = "CNY"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash-multiple"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_cost"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            val = self.coordinator.data.get("total_cost")
            if val is not None:
                return float(val)
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data:
            return {"cost_by_service": self.coordinator.data.get("cost_by_service")}
        return None


class TotalTrafficSensor(AliyunBillEntity):
    """Sensor for total monthly outbound traffic."""

    _attr_name = "Current Month Outbound Traffic"
    _attr_native_unit_of_measurement = "GB"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:network-outline"

    def __init__(
        self, coordinator: AliyunDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_traffic"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("total_traffic_gb")
        return None


class ServiceCostSensor(AliyunBillEntity):
    """Sensor for cost of a specific service."""

    _attr_native_unit_of_measurement = "CNY"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash"

    def __init__(
        self, coordinator: AliyunDataUpdateCoordinator, entry: ConfigEntry, service_code: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self.service_code = service_code
        
        # Set name from coordinator data, fallback to service_code
        cost_data = coordinator.data.get("cost_by_service", {}).get(service_code, {})
        self._attr_name = cost_data.get('name', f"{service_code} Cost")
        
        self._attr_unique_id = f"{entry.entry_id}_cost_{service_code.lower()}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "cost_by_service" in self.coordinator.data:
            service_info = self.coordinator.data["cost_by_service"].get(self.service_code)
            if service_info:
                return service_info.get("cost")
        return None