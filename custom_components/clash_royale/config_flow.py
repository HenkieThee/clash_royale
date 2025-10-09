"""Config flow for Clash Royale integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

_LOGGER = logging.getLogger(__name__)

APITOKEN_SCHEMA = vol.Schema({
    vol.Required("api_token", description="Your Clash Royale API token from developer.clashroyale.com"): str,
})

PLAYER_SCHEMA = vol.Schema({
    vol.Required("player_tag", description="Player tag (e.g. #28GOJ92JY or 28GOJ92JY)"): str,
})

class ClashRoyaleConfigFlow(config_entries.ConfigFlow, domain="clash_royale"):
    """Handle config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.api_token = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Check if the integration already has an API token
        existing_entries = self._async_current_entries()
        
        if existing_entries:
            # Already exists, get API token
            self.api_token = existing_entries[0].data.get("api_token")
            if self.api_token:
                return await self.async_step_player()
        
        # API token not found, ask for it
        return await self.async_step_setup()

    async def async_step_setup(self, user_input=None):
        """Handle the setup step for API token."""
        errors = {}
        
        if user_input is not None:
            api_token = user_input.get("api_token")
            
            if not api_token:
                errors["base"] = "missing_data"
            else:
                # Validate API token
                validation_result = await self._validate_api_token(api_token)
                if validation_result["valid"]:
                    self.api_token = api_token
                    return await self.async_step_player()
                else:
                    errors.update(validation_result["errors"])
        
        return self.async_show_form(
            step_id="setup", 
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
                    validation_result = await self._validate_player_tag(player_tag)
                    if validation_result["valid"]:
                        return self.async_create_entry(
                            title=f"Player {player_tag}", 
                            data={
                                "api_token": self.api_token,
                                "player_tag": player_tag
                            }
                        )
                    else:
                        errors.update(validation_result["errors"])
        
        return self.async_show_form(
            step_id="player", 
            data_schema=PLAYER_SCHEMA,
            errors=errors
        )

    async def _validate_api_token(self, api_token: str) -> dict:
        """Validate the API token by making a dummy request."""
        try:
            session = async_get_clientsession(self.hass)
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json"
            }
            
            # Test with dummy request
            url = "https://api.clashroyale.com/v1/players/%23dummy"
            
            async with session.get(url, headers=headers) as response:
                if response.status == 403:
                    return {"valid": False, "errors": {"api_token": "invalid_token"}}
                elif response.status in [400, 404, 200]:
                    # Token is valid
                    return {"valid": True, "errors": {}}
                else:
                    return {"valid": False, "errors": {"base": "api_error"}}
                    
        except Exception as err:
            _LOGGER.error(f"Connection error during API token validation: {err}")
            return {"valid": False, "errors": {"base": "connection_error"}}

    async def _validate_player_tag(self, player_tag: str) -> dict:
        """Validate the player tag by checking if the player exists."""
        try:
            session = async_get_clientsession(self.hass)
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            }
            
            encoded_tag = player_tag.replace("#", "%23")
            url = f"https://api.clashroyale.com/v1/players/{encoded_tag}"
            
            async with session.get(url, headers=headers) as response:
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
        - #28GOJ92JY 
        - 28GOJ92JY
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
    
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required("interval", default=self.config_entry.options.get("interval", 300)): int
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)
