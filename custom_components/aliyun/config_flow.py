"""Config flow for Alibaba Cloud."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN

from .api import AliyunApiError, AliyunAuthError, AliyunBssApiClient
from .const import DOMAIN, CONF_ACCESS_KEY_ID, CONF_ACCESS_KEY_SECRET, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES


class AliyunBillConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alibaba Cloud."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Prevent duplicate entries for the same Access Key ID
            await self.async_set_unique_id(user_input[CONF_ACCESS_KEY_ID])
            self._abort_if_unique_id_configured()

            try:
                api_client = AliyunBssApiClient(
                    access_key_id=user_input[CONF_ACCESS_KEY_ID],
                    access_key_secret=user_input[CONF_ACCESS_KEY_SECRET],
                    hass=self.hass,
                )
                if await api_client.test_authentication():
                    return self.async_create_entry(
                        title=user_input[CONF_ACCESS_KEY_ID], data=user_input
                    )
            except AliyunAuthError:
                errors["base"] = "invalid_auth"
            except AliyunApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        # The form schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_KEY_ID): str,
                vol.Required(CONF_ACCESS_KEY_SECRET): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_HOURS): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return AliyunBillOptionsFlowHandler(config_entry)


class AliyunBillOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Alibaba Cloud integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
