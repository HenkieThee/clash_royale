"""Clash Royale sensor platform."""
from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class ClashRoyaleDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for fetching data."""
    
    def __init__(self, hass: HomeAssistant, api_token: str, player_tag: str, update_interval: int = 300, proxy_url: str = None):
        """Initialize the coordinator."""
        self.api_token = api_token
        self.player_tag = player_tag.replace("#", "%23")  # URL encode the #
        self.proxy_url = proxy_url
        
        super().__init__(
            hass,
            _LOGGER,
            name="clash_royale",
            update_interval=timedelta(seconds=update_interval),
        )
    
    async def _async_update_data(self):
        """Fetch data from the API."""
        try:
            session = async_get_clientsession(self.hass)
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            }
            
            url = f"https://api.clashroyale.com/v1/players/{self.player_tag}"
            
            async with session.get(url, headers=headers, proxy=self.proxy_url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 403:
                    error_msg = await response.text()
                    _LOGGER.error(f"Invalid API token (403 Forbidden): {error_msg}")
                    raise UpdateFailed(f"Invalid API token: {error_msg}")
                elif response.status == 404:
                    _LOGGER.error("Player not found (404)")
                    raise UpdateFailed(f"Player {self.player_tag} not found")
                else:
                    _LOGGER.error(f"API error: {response.status}")
                    raise UpdateFailed(f"API returned status {response.status}")
        
        except UpdateFailed:
            # Re-raise UpdateFailed without wrapping it again or logging it again
            raise
        except Exception as err:
            _LOGGER.error(f"Error fetching data: {err}")
            raise UpdateFailed(f"Error fetching data: {err}")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors from a config entry."""
    # Use data from the entry setup in __init__.py if available, or direct from entry
    # Best practice is to get coordinator from hass.data if setup there, but currently
    # the coordinator is created here.
    
    api_token = entry.data.get("api_token")
    player_tag = entry.data.get("player_tag")
    
    # Get update interval from options (default 300 seconds)
    update_interval = entry.options.get("interval", 300)
    
    # Get proxy url from options or config
    proxy_url = entry.options.get("proxy_url", entry.data.get("proxy_url"))
    if proxy_url == "":
        proxy_url = None
    
    # Create coordinator for shared data updates
    coordinator = ClashRoyaleDataUpdateCoordinator(hass, api_token, player_tag, update_interval, proxy_url)
    await coordinator.async_config_entry_first_refresh()
    
    # Add one sensor per player with all data as attributes
    async_add_entities([
        ClashRoyalePlayerSensor(coordinator),
    ])

class ClashRoyalePlayerSensor(SensorEntity):
    """Player sensor with all stats as attributes."""
    
    def __init__(self, coordinator: ClashRoyaleDataUpdateCoordinator):
        """Initialize the sensor."""
        self.coordinator = coordinator
        player_tag = coordinator.player_tag.replace("%23", "#")
        self._attr_name = f"Clash Royale {player_tag}"
        self._attr_unique_id = f"clash_royale_{player_tag}".replace("#", "")
        self._attr_should_poll = False 
        self._attr_icon = "mdi:crown"

    @property
    def native_value(self):
        """Return the main value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("trophies")

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement for the main value."""
        return "trophies"

    @property
    def extra_state_attributes(self):
        """Return all other stats as attributes."""
        if not self.coordinator.data:
            return {}
            
        data = self.coordinator.data
        attributes = {
            "player_name": data.get("name", "Unknown"),
            "player_tag": data.get("tag", ""),
            "level": data.get("expLevel", 1),
            "trophies": data.get("trophies", 0),
            "best_trophies": data.get("bestTrophies", 0),
            "wins": data.get("wins", 0),
            "losses": data.get("losses", 0),
            "battle_count": data.get("battleCount", 0),
            "three_crown_wins": data.get("threeCrownWins", 0),
            "challenge_cards_won": data.get("challengeCardsWon", 0),
            "challenge_max_wins": data.get("challengeMaxWins", 0),
            "tournament_cards_won": data.get("tournamentCardsWon", 0),
            "tournament_battle_count": data.get("tournamentBattleCount", 0),
            "donations": data.get("donations", 0),
            "donations_received": data.get("donationsReceived", 0),
            "total_donations": data.get("totalDonations", 0),
        }
        
        # Add clan information if available
        if "clan" in data and data["clan"]:
            clan = data["clan"]
            attributes.update({
                "clan_name": clan.get("name", "No Clan"),
                "clan_tag": clan.get("tag", ""),
                "clan_role": clan.get("role", "member"),
                "clan_badge_id": clan.get("badgeId", 0),
            })
        else:
            # Player is not in a clan
            attributes.update({
                "clan_name": "No Clan",
                "clan_tag": "",
                "clan_role": "none",
                "clan_badge_id": 0,
            })
        
        # Filter out None values
        return {k: v for k, v in attributes.items() if v is not None}

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """When sensor is added to Home Assistant."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
