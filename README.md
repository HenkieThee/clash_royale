# Clash Royale Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/HenkieThee/Clash_Royale_HA.svg)](https://github.com/HenkieThee/Clash_Royale_HA/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.4.4%2B-blue.svg)](https://github.com/home-assistant/core)

A Home Assistant integration that fetches Clash Royale player statistics using the official Clash Royale API.

## Features

- 🏆 **Player Statistics**: Track trophies, wins, losses, and more
- 👑 **Clan Information**: View clan membership and role
- 📊 **Real-time Updates**: Configurable update intervals
- 🎮 **Multiple Players**: Support for multiple player accounts
- 🔒 **Proxy Support**: Route traffic through a static IP (perfect for dynamic home IPs)
- ⚙️ **Easy Configuration**: Simple setup through Home Assistant UI

## Installation

### HACS (Recommended)

1. Open HACS → Integrations → Search for "Clash Royale"
2. Install and restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/HenkieThee/Clash_Royale_HA/releases)
2. Copy the `clash_royale` folder to your `config/custom_components/` directory
3. Restart Home Assistant

## Setup

### 1. Get Your API Token

1. Visit the [Clash Royale Developer Portal](https://developer.clashroyale.com/)
2. Create an account or log in
3. Click on **My Account**
4. Create a new API key
5. **Important**: Add your Home Assistant IP address (or your VPS Proxy IP) to the allowed IPs list

### 2. Configure the Integration

1. Go to **Settings** → **Devices & Services** in Home Assistant
2. Click **Add Integration**
3. Search for "Clash Royale"
4. Enter your API token when prompted
5. Enter your player tag (format: `#28g0j92jy` or `28g0j92jy`)
6. **(Optional)** Enter your Proxy URL if you need to route traffic through a static IP (e.g., `http://user:pass@ip:port`)
7. Click **Submit**

### 3. Find Your Player Tag

Your player tag can be found in the Clash Royale app:
- Open Clash Royale
- Tap on your profile
- Your player tag is displayed at the top (e.g., `#28g0j92jy`)

## Proxy Support (Dynamic IP Solution)

The Clash Royale API requires you to whitelist a **Static IP address**. If your home internet has a **Dynamic IP** (which changes periodically), your API token will stop working when your IP changes.

To fix this, you can configure this integration to route traffic through a proxy server (e.g., Squid) hosted on a VPS with a static IP. This integration supports standard HTTP proxies with authentication.

**Example Configuration:**
If you set up Squid on a VPS with username/password auth, your URL will look like this:
`http://username:password@87.106.207.220:3128`

## Configuration Options
The integration supports the following configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| Update Interval | How often to fetch data (seconds) | 300 (5 minutes) |

To change options:
1. Go to **Settings** → **Devices & Services**
2. Find your Clash Royale integration
3. Click **Configure**
4. Adjust the update interval as needed

## Available Data

The integration creates a sensor for each configured player with the following information:

### Main Sensor Value
- **Trophies**: Current trophy count

### Attributes
- **Player Information**:
  - Player name
  - Player tag
  - Level
  - Current trophies
  - Best trophies
  
- **Battle Statistics**:
  - Wins
  - Losses
  - Battle count
  - Three crown wins
  
- **Tournament & Challenge Data**:
  - Challenge cards won
  - Challenge max wins
  - Tournament cards won
  - Tournament battle count
  
- **Clan Information**:
  - Clan name
  - Clan tag
  - Clan role
  - Clan badge ID
  
- **Donations**:
  - Current season donations
  - Donations received
  - Total donations

## Example Usage

### Lovelace Card

```yaml
type: entities
title: Clash Royale Stats
entities:
  - entity: sensor.clash_royale_28g0j92jy
    name: "Current Trophies"
  - type: attribute
    entity: sensor.clash_royale_28g0j92jy
    attribute: player_name
    name: "Player Name"
  - type: attribute
    entity: sensor.clash_royale_28g0j92jy
    attribute: clan_name
    name: "Clan"
  - type: attribute
    entity: sensor.clash_royale_28g0j92jy
    attribute: wins
    name: "Total Wins"
```

### Automation Example

```yaml
automation:
  - alias: "Clash Royale Trophy Milestone"
    trigger:
      - platform: numeric_state
        entity_id: sensor.clash_royale_28g0j92jy
        above: 5000
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "🏆 Congratulations! You've reached {{ states('sensor.clash_royale_28g0j92jy') }} trophies!"
```

## Troubleshooting

### Common Issues

1. **"Invalid API token" error**
   - Verify your API token is correct
   - Check that your Home Assistant IP is in the allowed IPs list on the developer portal
   - Make sure the API key hasn't expired

2. **"Player not found" error**
   - Double-check your player tag format
   - Ensure the player tag exists and is spelled correctly

3. **Data not updating**
   - Check your internet connection
   - Verify the Clash Royale API status
   - Review Home Assistant logs for error messages

## Disclaimer

This integration is **NOT affiliated with, endorsed, or sponsored by Supercell or Clash Royale**. This is an unofficial third-party integration that uses the publicly available Clash Royale API.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Search existing [issues](https://github.com/HenkieThee/Clash_Royale_HA/issues)
3. Create a new issue with detailed information
