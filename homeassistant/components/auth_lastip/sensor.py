"""A sensor for the Last IP"""
import logging
import os

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

import voluptuous as vol

CONF_EXCLUDE = "exclude"

_LOGGER = logging.getLogger(__name__)

PLATFORM_NAME = "auth_lastip"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_EXCLUDE, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)

def setup_platform(hass, config, add_devices, discovery_info=None):

    def authenticated_async_log_refresh_token_usage(refresh_token, remote_ip):
        _LOGGER.info(f"Authenticated token refreshed for {refresh_token.user.name} (IP {remote_ip})")
        r = original_async_log_refresh_token_usage(refresh_token, remote_ip)
        sensor.update_state(refresh_token, remote_ip)
        return r

    """Create the sensor"""
    exclude = config.get(CONF_EXCLUDE)

    sensor = AuthLastIPSensor(hass, exclude)

    # inject the token refresh
    original_async_log_refresh_token_usage = hass.auth._store.async_log_refresh_token_usage
    hass.auth._store.async_log_refresh_token_usage = authenticated_async_log_refresh_token_usage

    add_devices([sensor], True)


class AuthLastIPSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, hass, exclude):
        """Initialize the sensor."""
        self.hass = hass
        self.entity_id = "sensor.auth_lastip"
        self._state = None
        self._token = None
        self.exclude = exclude

    def update_state(self, refresh_token, remote_ip):
        if remote_ip in self.exclude:
            return
        self._state = remote_ip
        self._token = refresh_token
        self.async_write_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Last authentication IP address"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:lock-alert"

    @property
    def extra_state_attributes(self):
        """Return attributes for the sensor."""
        if self._state is None:
            return None
        return {
            "user_id": self._token.user.id,
            "username": self._token.user.name,
            "client_id": self._token.client_id,
            "client_name": self._token.client_name,
            "client_icon": self._token.client_icon
        }
