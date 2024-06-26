import aiohttp
import asyncio
from datetime import timedelta
import json
import logging
import re
import time
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import async_load_platform

REQUIREMENTS = [ ]

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Data provided by vizmuvek.hu"
CONF_NAME = 'name'
CONF_REGION = 'region'
CONF_SSL = 'ssl'

DEFAULT_NAME = 'Water Quality FVM'
DEFAULT_REGION = "Budapest - I. kerület"
DEFAULT_ICON = 'mdi:water'
DEFAULT_SSL = True

HTTP_TIMEOUT = 60 # secs
MAX_RETRIES = 3
SCAN_INTERVAL = timedelta(hours=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_REGION, default=DEFAULT_REGION): cv.string,
    vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
})

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    region = config.get(CONF_REGION)
    ssl = config.get(CONF_SSL)

    async_add_devices(
        [WaterQualityFVMSensor(hass, name, region, ssl )],update_before_add=True)

def _sleep(secs):
    time.sleep(secs)

async def async_get_wqdata(self):
    wqjson = {}
    jsonstr = None
    l2print = False

    _session = async_get_clientsession(self._hass, self._ssl)

    url = 'https://www.vizmuvek.hu/hu/kezdolap/informaciok/vizminoseg-vizkemenyseg'
    for i in range(MAX_RETRIES):
      try:
        async with _session.get(url, timeout=HTTP_TIMEOUT) as response:
          rsp1 = await response.text()

        if not response.status // 100 == 2:
          _LOGGER.debug("Fetch attempt " + str(i+1) + ":unexpected responsefailed " + str(response.status))
          await self._hass.async_add_executor_job(_sleep, 10)
        else:
          break
      except Exception as err:
        rsp1 = ""
        _LOGGER.debug("Fetch attempt " + str(i+1) + " failed for " + url)
        _LOGGER.error(f'error: {err} of type: {type(err)}')
        await self._hass.async_add_executor_job(_sleep, 10)

    rsp = rsp1.split("\n")

    for ind, line in enumerate(rsp):
      if self._region.lower() in line.lower():
        _LOGGER.debug("location: " + line)
        jsonstr = '{\"location\":\"' + _get_location(line.lstrip()) + '\",' + \
          '\"water_quality\":['
        l2print = True
      elif l2print:
        _LOGGER.debug(jsonstr)
        jsonstr += _get_wquality(line.lstrip())
        if 'pH</td>' in line:
          l2print = False
          jsonstr += ']}'
        else:
          jsonstr += ','
      if jsonstr is not None:
        _LOGGER.debug("result: " + str(jsonstr))
    if jsonstr is not None:
      _LOGGER.debug("jsonstr: " + jsonstr)
      wqjson = json.loads(jsonstr.replace(',,,,',',').replace('},]}','}]}'))
    return wqjson

def _get_location(region):
  return region.replace('<tr><th colspan="3">','').\
      replace('</th></tr>','')

def _get_wquality(wqstring):
  HTMLCOMMENT = re.compile('<!--.*-->')
  wqstring1 = re.sub(HTMLCOMMENT,'',wqstring)

  wqstring2 = wqstring1.replace('<tr><td class="name">','{\"name\":\"').\
      replace('</td><td class="value text-right">','\",\"value\":\"').\
      replace('</td></tr>','\"}')

  NUMBER = re.compile('([0-9]+,*[0-9]*) ')
  wqstring = re.sub(NUMBER,'\\1\",\"unit\":\"',wqstring2)

  return wqstring

def _get_wq_limit(argument):
    switcher = {
      "Szabad aktív klór": "1000",
      "Klorid": "100", # mg/l
      "Vas": "200", # ug/l
      "Mangán": "50", # ug/l
      "Nitrát": "50", # mg/l
      "Nitrit": "0.1", # mg/l
      "Ammónium": "0.2", # mg/l
      "Összes keménység": "350", # mg/l CaO
      "Vezetőképesség": "2500", # ug/cm
      "pH": "8.5",
    }
    return switcher.get(argument)

class WaterQualityFVMSensor(Entity):

    def __init__(self, hass, name, region, ssl):
        """Initialize the sensor."""
        self._hass = hass
        self._name = name
        self._region = region
        self._state = None
        self._wqdata = []
        self._icon = DEFAULT_ICON
        self._ssl = ssl
        self._kemenyseg = ''

    @property
    def extra_state_attributes(self):
        attr = {}

        if 'water_quality' in self._wqdata:
            attr["water_quality"] = self._wqdata.get('water_quality')
            attr["location"] = self._wqdata.get('location')
            attr["water_hardness"] = self._kemenyseg

        attr["provider"] = CONF_ATTRIBUTION
        return attr

    async def async_update(self):
        wqdata = await async_get_wqdata(self)
        out_of_range = 0

        self._wqdata = wqdata
        if 'water_quality' in self._wqdata:
            for item in self._wqdata['water_quality']:
                val = item.get('value').replace(',','.').replace('<','')
                item['limit'] = _get_wq_limit(item.get('name'))
                if 'Összes keménység' in item.get('name'):
                    kemenysegstr = ''
                    if int(val) > 300:
                        kemenystr = "nagyon kemény"
                    elif int(val) > 180:
                        kemenystr = "kemény"
                    elif int(val) > 80:
                        kemenystr = "közepesen kemény"
                    elif int(val) > 40:
                        kemenystr = "lágy"
                    elif int(val) > 0:
                        kemenystr = "nagyon lágy"
                    self._kemenyseg = kemenystr

                item['state'] = "ok"
                if item.get('limit') is not None:
                    if float(val) > float(item.get('limit')):
                        item['state'] = "out of range"
                        out_of_range += 1
                    else:
                        item['state'] = "ok"

        self._state = out_of_range
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        if int(self._state) > 0:
            return "mdi:water-alert"
        return DEFAULT_ICON
