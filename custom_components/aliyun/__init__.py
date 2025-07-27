"""The Alibaba Cloud integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import AliyunBssApiClient
from .const import DOMAIN, PLATFORMS, CONF_ACCESS_KEY_ID, CONF_ACCESS_KEY_SECRET
from .coordinator import AliyunDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alibaba Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create an API client instance for this entry
    api_client = AliyunBssApiClient(
        access_key_id=entry.data[CONF_ACCESS_KEY_ID],
        access_key_secret=entry.data[CONF_ACCESS_KEY_SECRET],
        hass=hass,
    )

    # Create a DataUpdateCoordinator
    coordinator = AliyunDataUpdateCoordinator(hass, api_client=api_client, entry=entry)
    
    # Fetch initial data so we have it before entities are set up
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data for the platforms to access
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        # No migration needed yet, but good to have the placeholder
        entry.version = 1

    _LOGGER.debug("Migration to version %s successful", entry.version)

    return True