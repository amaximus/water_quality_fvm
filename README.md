[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

<p><a href="https://www.buymeacoffee.com/6rF5cQl" rel="nofollow" target="_blank"><img src="https://camo.githubusercontent.com/c070316e7fb193354999ef4c93df4bd8e21522fa/68747470733a2f2f696d672e736869656c64732e696f2f7374617469632f76312e7376673f6c6162656c3d4275792532306d6525323061253230636f66666565266d6573736167653d25463025394625413525413826636f6c6f723d626c61636b266c6f676f3d6275792532306d6525323061253230636f66666565266c6f676f436f6c6f723d7768697465266c6162656c436f6c6f723d366634653337" alt="Buy me a coffee" data-canonical-src="https://img.shields.io/static/v1.svg?label=Buy%20me%20a%20coffee&amp;message=%F0%9F%A5%A8&amp;color=black&amp;logo=buy%20me%20a%20coffee&amp;logoColor=white&amp;labelColor=b0c4de" style="max-width:100%;"></a></p>

# Water Quality FVM (Budapest, HU) custom integration for Home Assistant

This custom component integrates water quality information provided by Budapest Water Company (FVM - Fővárosi Vízművek).

The state of the sensor will be the number of monitored items above their threshold. Thresholds are defined on the `FVM vízminőség, vízkeménység` page (see below).

State of a water quality element can be either `ok` or `out of range`.

Water hardness value is listed with other monitored elements, while the human readable water hardness string is listed as a standalone attribute.

#### Installation
The easiest way to install it is through [HACS (Home Assistant Community Store)](https://github.com/hacs/integration),
search for <i>Water Quality FVM</i> in the Integrations.<br />

#### Configuration:
Define sensor with the following configuration parameters:<br />

---
| Name | Optional | `Default` | Description |
| :---- | :---- | :------- | :----------- |
| name | **Y** | `water_quality_fvm` | name of the sensor |
| region | **Y** | `Budapest - I. kerület` | region string (see below) |
| ssl | **Y** | `true` | control SSL verification. This is useful when CA store update with new root/intermediate certificates is problematic. WARNING: setting this to `false` is a security breach. |
---

Region should match the location specified at [FVM vízminőség, keménység](https://www.vizmuvek.hu/hu/kezdolap/informaciok/vizminoseg-vizkemenyseg).

Example of water quality information:

![Water quality attributes](https://raw.githubusercontent.com/amaximus/water_quality_fvm/main/water_quality_attrs.png)

## Examples
```
platform: water_quality_fvm
region: 'Budapest - XXII. kerület'
```

Example Lovelace UI conditional custom button card:
```
type: conditional
conditions:
  - entity: sensor.water_quality_fvm
    state_not: '0'
card:
  type: custom:button-card
  color_type: icon
  show_label: true
  show_name: false
  show_icon: true
  entity: sensor.water_quality_fvm
  size: 30px
  styles:
    label:
      - font-size: 90%
      - text-align: left
    card:
      - height: 80px
    icon:
      - color: var(--paper-item-icon-active-color)
  layout: icon_label
  label: >
    [[[
      var label = ""
      var w_alerts = states['sensor.water_quality_fvm'].attributes.water_quality;
      for (var k=0; k < states['sensor.water_quality_fvm'].state; k++) {
        if ( w_alerts[k].state != "ok" ) {
          label += w_alerts[k].name + ": " + w_alerts[k].value + " " +
                   w_alerts[k].unit + "&nbsp;&nbsp;(" + w_alerts[k].limit +
                   " " + w_alerts[k].unit + ")" + `<br>`
        }
      }
      return label;
    ]]]
```

## Thanks

Thanks to all the people who have contributed!

[![contributors](https://contributors-img.web.app/image?repo=amaximus/anniversary)](https://github.com/amaximus/anniversary/graphs/contributors)
