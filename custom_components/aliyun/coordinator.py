"""DataUpdateCoordinator for the Alibaba Cloud integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AliyunApiError, AliyunBssApiClient
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class AliyunDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Aliyun BSS API."""

    def __init__(self, hass: HomeAssistant, api_client: AliyunBssApiClient, entry: ConfigEntry) -> None:
        """Initialize."""
        self.api_client = api_client
        update_interval = timedelta(minutes=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        data = await self.api_client.get_current_month_data()
        return data
