"""Config flow for Clash Royale integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

_LOGGER = logging.getLogger(__name__)

PROXY_SCHEMA = vol.Schema({
    vol.Optional("proxy_url", description="Proxy URL (e.g. http://user:pass@host:port)"): str,
})

APITOKEN_SCHEMA = vol.Schema({
    vol.Required("api_token", description="Your Clash Royale API token from developer.clashroyale.com"): str,
})

PLAYER_SCHEMA = vol.Schema({
    vol.Required("player_tag", description="Player tag (e.g. #28g0j92jy or 28g0j92jy)"): str,
})

class ClashRoyaleConfigFlow(config_entries.ConfigFlow, domain="clash_royale"):
    """Handle config flow."""
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.api_token = None
        self.proxy_url = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Check if the integration already has an API token
        existing_entries = self._async_current_entries()
        
        if existing_entries:
            # Already exists, get API token and proxy
            self.api_token = existing_entries[0].data.get("api_token")
            self.proxy_url = existing_entries[0].data.get("proxy_url")
            if self.api_token:
                return await self.async_step_player()
        
        # Start with proxy setup
        return await self.async_step_proxy()

    async def async_step_proxy(self, user_input=None):
        """Handle the proxy setup step."""
        errors = {}
        
        if user_input is not None:
            self.proxy_url = user_input.get("proxy_url")
            if not self.proxy_url:
                self.proxy_url = None
            return await self.async_step_token()

        return self.async_show_form(
            step_id="proxy",
            data_schema=PROXY_SCHEMA,
            errors=errors
        )

    async def async_step_token(self, user_input=None):
        """Handle the API token step."""
        errors = {}
        
        if user_input is not None:
            api_token = user_input.get("api_token")
            
            if not api_token:
                errors["base"] = "missing_data"
            else:
                # Validate API token using the proxy (if set)
                validation_result = await self._validate_api_token(api_token, self.proxy_url)
                if validation_result["valid"]:
                    self.api_token = api_token
                    return await self.async_step_player()
                else:
                    errors.update(validation_result["errors"])
        
        return self.async_show_form(
            step_id="token", 
            data_schema=APITOKEN_SCHEMA,
            errors=errors
        )

    async def async_step_player(self, user_input=None):
        """Handle the player tag step."""
        errors = {}
        
        if user_input is not None:
            player_tag = user_input.get("player_tag")
            
            if not player_tag:
                errors["base"] = "missing_data"
            else:
                # Normalize player tag
                player_tag = self._normalize_player_tag(player_tag)
                
                # Check if player already exists
                if self._is_player_already_configured(player_tag):
                    errors["player_tag"] = "already_configured"
                else:
                    # Validate player tag
                    validation_result = await self._validate_player_tag(player_tag, self.proxy_url)
                    if validation_result["valid"]:
                        return self.async_create_entry(
                            title=f"Player {player_tag}", 
                            data={
                                "api_token": self.api_token,
                                "player_tag": player_tag,
                                "proxy_url": self.proxy_url
                            }
                        )
                    else:
                        errors.update(validation_result["errors"])
        
        return self.async_show_form(
            step_id="player", 
            data_schema=PLAYER_SCHEMA,
            errors=errors
        )

    async def _validate_api_token(self, api_token: str, proxy_url: str = None) -> dict:
        """Validate the API token by making a dummy request."""
        try:
            session = async_get_clientsession(self.hass)
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json"
            }
            
            # Test with dummy request
            url = "https://api.clashroyale.com/v1/players/%23dummy"
            
            async with session.get(url, headers=headers, proxy=proxy_url) as response:
                if response.status == 403:
                    error_msg = await response.text()
                    _LOGGER.error(f"API validation failed with 403: {error_msg}")
                    return {"valid": False, "errors": {"api_token": "invalid_token"}}
                elif response.status in [400, 404, 200]:
                    # Token is valid
                    return {"valid": True, "errors": {}}
                else:
                    _LOGGER.error(f"API validation failed with status {response.status}")
                    return {"valid": False, "errors": {"base": "api_error"}}
                    
        except Exception as err:
            _LOGGER.error(f"Connection error during API token validation: {err}")
            return {"valid": False, "errors": {"base": "connection_error"}}

    async def _validate_player_tag(self, player_tag: str, proxy_url: str = None) -> dict:
        """Validate the player tag by checking if the player exists."""
        try:
            session = async_get_clientsession(self.hass)
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            }
            
            encoded_tag = player_tag.replace("#", "%23")
            url = f"https://api.clashroyale.com/v1/players/{encoded_tag}"
            
            async with session.get(url, headers=headers, proxy=proxy_url) as response:
                if response.status == 404:
                    return {"valid": False, "errors": {"player_tag": "player_not_found"}}
                elif response.status == 200:
                    return {"valid": True, "errors": {}}
                else:
                    return {"valid": False, "errors": {"base": "api_error"}}
                    
        except Exception as err:
            _LOGGER.error(f"Connection error during player validation: {err}")
            return {"valid": False, "errors": {"base": "connection_error"}}

    def _normalize_player_tag(self, player_tag: str) -> str:
        """Normalize player tag to always start with #.
        
        Accepts both formats:
        - #28g0j92jy 
        - 28g0j92jy
        """
        player_tag = player_tag.strip() 
        if not player_tag.startswith("#"):
            return f"#{player_tag}"
        return player_tag

    def _is_player_already_configured(self, player_tag: str) -> bool:
        """Check if the player tag is already configured."""
        existing_entries = self._async_current_entries()
        for entry in existing_entries:
            if entry.data.get("player_tag") == player_tag:
                return True
        return False

    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ClashRoyaleOptionsFlowHandler(config_entry)


class ClashRoyaleOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""
    
    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required("interval", default=self.config_entry.options.get("interval", 300)): int,
            vol.Optional("proxy_url", default=self.config_entry.options.get("proxy_url") or self.config_entry.data.get("proxy_url") or ""): str,
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)
