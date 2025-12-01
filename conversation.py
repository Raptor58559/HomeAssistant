from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.components import conversation as hass_conversation
from homeassistant.components.conversation import ConversationEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_AGENT_ID,
    OLLAMA_URL,
    OLLAMA_MODEL,
    CONF_PROMPT,
    DEFAULT_PROMPT,
    CONF_MODEL,
    CONF_NUM_PREDICT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_NUM_PREDICT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the proxy conversation entity from a config entry."""
    async_add_entities([OllamaProxyConversationEntity(hass, entry)])


class OllamaProxyConversationEntity(ConversationEntity):
    """Proxy that rewrites user text via Ollama, then calls the default HA agent."""

    _attr_has_entity_name = True
    _attr_name = "Ollama Proxy Conversation"
    _attr_unique_id = "ollama_proxy_conversation_agent"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages (must be a list for HA's matcher)."""
        return ["en-GB", "en", "de-AT", "de"]

    # ---------- Helper: cleanup & validate Ollama output ----------

    def _cleanup_ollama_output(self, content: Any, original: str) -> tuple[bool, str]:
        """Normalize and validate Ollama output.

        Returns (ok, final_text).

        ok == False, final_text == "__APOLOGY__":
            -> treat as gibberish, trigger apology.

        ok == False, final_text == original:
            -> degrade gracefully to default agent with original text.
        """
        if not isinstance(content, str):
            _LOGGER.warning("OLLAMA CONTENT IS NOT STRING: %r", content)
            return False, original

        raw = content.strip()
        if not raw:
            _LOGGER.warning("OLLAMA CONTENT EMPTY")
            return False, original

        # Special case: explicit no-command signal
        if raw.upper() == "NO_COMMAND":
            # Heuristic: if original looks like short gibberish, trigger apology;
            # otherwise fall back to default agent with original text.
            cleaned_orig = original.strip()
            token_count = len(cleaned_orig.split())
            length = len(cleaned_orig)

            # Example gibberish: "asdasd", "qwer", "blablubb"
            if token_count <= 2 and length <= 8:
                _LOGGER.warning(
                    "OLLAMA NO_COMMAND and input looks like gibberish; using apology fallback"
                )
                return False, "__APOLOGY__"

            _LOGGER.warning(
                "OLLAMA NO_COMMAND but input looks like normal sentence; "
                "falling back to original text"
            )
            return False, original

        # Remove code fences if present
        if "```" in raw:
            _LOGGER.warning("OLLAMA CONTENT CONTAINS CODE FENCE, STRIPPING")
            raw = raw.replace("```", "").strip()

        # If there are multiple lines, keep only the first
        if "\n" in raw:
            first_line = raw.splitlines()[0].strip()
            _LOGGER.warning("OLLAMA MULTILINE OUTPUT, USING FIRST LINE: %r", first_line)
            raw = first_line

        lower = raw.lower()

        # Strip typical role prefixes
        for prefix in ("assistant:", "assistant ", "user:", "user "):
            if lower.startswith(prefix):
                _LOGGER.warning("OLLAMA OUTPUT HAD ROLE PREFIX, STRIPPING: %r", raw)
                raw = raw[len(prefix):].lstrip()
                lower = raw.lower()
                break

        # Strip surrounding quotes / backticks
        if (
            len(raw) > 2
            and raw[0] in ("'", '"', "`")
            and raw[-1] in ("'", '"', "`")
        ):
            _LOGGER.warning("OLLAMA OUTPUT WRAPPED IN QUOTES, STRIPPING: %r", raw)
            raw = raw[1:-1].strip()
            lower = raw.lower()

        # Hard reject JSON-like structures
        if raw.startswith("{") or raw.startswith("[") or '"role":' in lower:
            _LOGGER.warning("OLLAMA OUTPUT LOOKS LIKE JSON/STRUCTURED: %r", raw)
            return False, original

        # Strip trailing sentence punctuation from the end (.?!)
        cleaned = raw.rstrip(".?!").strip()

        if not cleaned:
            _LOGGER.warning("OLLAMA CLEANED OUTPUT BECAME EMPTY, FALLING BACK")
            return False, original

        # Avoid insanely long stuff (likely explanation)
        if len(cleaned) > 200:
            _LOGGER.warning(
                "OLLAMA OUTPUT TOO LONG (%d chars), FALLING BACK", len(cleaned)
            )
            return False, original

        _LOGGER.warning("OLLAMA CLEAN OUTPUT ACCEPTED: %r -> %r", content, cleaned)
        return True, cleaned

    # ---------- Call Ollama ----------

    async def _call_ollama(self, text: str) -> tuple[bool, str]:
        """Send text to Ollama and return (success_flag, rewritten_text)."""

        _LOGGER.warning("OLLAMA INPUT: %r", text)

        # Read latest options on every call so GUI changes apply immediately
        opts = self.entry.options

        prompt = opts.get(CONF_PROMPT, DEFAULT_PROMPT)
        model = opts.get(CONF_MODEL, OLLAMA_MODEL)
        num_predict = opts.get(CONF_NUM_PREDICT, DEFAULT_NUM_PREDICT)
        temperature = opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        top_p = opts.get(CONF_TOP_P, DEFAULT_TOP_P)

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": prompt,
                },
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {
                "num_predict": int(num_predict),
                "temperature": float(temperature),
                "top_p": float(top_p),
            },
        }

        timeout_cfg = aiohttp.ClientTimeout(total=15)

        try:
            async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
                async with session.post(OLLAMA_URL, json=payload, timeout=15) as resp:
                    body = await resp.text()
                    _LOGGER.warning(
                        "OLLAMA HTTP STATUS: %s\nOLLAMA RAW BODY:\n%s",
                        resp.status,
                        body,
                    )

                    if resp.status != 200:
                        return False, text

                    data = await resp.json()

        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("OLLAMA EXCEPTION: %s", err)
            return False, text

        msg = data.get("message") or {}
        content = msg.get("content")
        _LOGGER.warning("OLLAMA RAW CONTENT: %r", content)

        ok, cleaned = self._cleanup_ollama_output(content, text)
        return ok, cleaned

    # ---------- Main entry point for conversation agent ----------

    async def async_process(self, user_input):
        """Process pipeline text → rewrite via Ollama → call default HA agent."""
        original = getattr(user_input, "text", "") or ""
        ctx = getattr(user_input, "context", None)
        conv_id = getattr(user_input, "conversation_id", None)
        language = getattr(user_input, "language", None)

        _LOGGER.debug("Received text from STT: %r", original)

        ok, rewritten = await self._call_ollama(original)

        _LOGGER.warning("ASYNC_PROCESS: ollama_ok=%s, rewritten=%r", ok, rewritten)

        # Fallback path
        if not ok:
            # Special marker: we decided this is gibberish -> apology
            if rewritten == "__APOLOGY__":
                apology = "Sorry, I made a mistake."
                return await hass_conversation.async_converse(
                    self.hass,
                    apology,
                    agent_id=DEFAULT_AGENT_ID,
                    conversation_id=conv_id,
                    context=ctx,
                    language=language,
                )

            # Otherwise: Ollama failed or said NO_COMMAND on a normal sentence.
            # Degrade gracefully to the default agent with the original text.
            return await hass_conversation.async_converse(
                self.hass,
                original,
                agent_id=DEFAULT_AGENT_ID,
                conversation_id=conv_id,
                context=ctx,
                language=language,
            )

        # Normal path: forward rewritten text to default assistant
        result = await hass_conversation.async_converse(
            self.hass,
            rewritten,
            agent_id=DEFAULT_AGENT_ID,
            conversation_id=conv_id,
            context=ctx,
            language=language,
        )

        return result
