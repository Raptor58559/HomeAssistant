from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_PROMPT,
    DEFAULT_PROMPT,
    CONF_MODEL,
    CONF_NUM_PREDICT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    OLLAMA_MODEL,
    DEFAULT_NUM_PREDICT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
)


class OllamaProxyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Ollama Proxy Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Single instance
            return self.async_create_entry(
                title="Ollama Proxy Conversation",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OllamaProxyOptionsFlow(config_entry)


class OllamaProxyOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Ollama Proxy Conversation."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        current_prompt = options.get(CONF_PROMPT, DEFAULT_PROMPT)
        current_model = options.get(CONF_MODEL, OLLAMA_MODEL)
        current_num_predict = options.get(CONF_NUM_PREDICT, DEFAULT_NUM_PREDICT)
        current_temperature = options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        current_top_p = options.get(CONF_TOP_P, DEFAULT_TOP_P)

        prompt_selector = selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        )

        num_predict_selector = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=4,
                max=256,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
            )
        )

        temperature_selector = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.0,
                max=1.0,
                step=0.05,
                mode=selector.NumberSelectorMode.SLIDER,
            )
        )

        top_p_selector = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1,
                max=1.0,
                step=0.05,
                mode=selector.NumberSelectorMode.SLIDER,
            )
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PROMPT,
                        default=current_prompt,
                    ): prompt_selector,
                    vol.Optional(
                        CONF_MODEL,
                        default=current_model,
                    ): str,
                    vol.Optional(
                        CONF_NUM_PREDICT,
                        default=current_num_predict,
                    ): num_predict_selector,
                    vol.Optional(
                        CONF_TEMPERATURE,
                        default=current_temperature,
                    ): temperature_selector,
                    vol.Optional(
                        CONF_TOP_P,
                        default=current_top_p,
                    ): top_p_selector,
                }
            ),
        )
