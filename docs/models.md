# Robot models

How other EZVIZ robots compare with the RS20 Max, worked out from the EZVIZ
app without the hardware. Use it as the starting point when someone reports a
model.

## Which app plugin each model uses

The EZVIZ app (7.6.3) picks a control plugin from the robot's sub-category:

| Sub-category | Plugin | Version checked |
|---|---|---|
| RS20 Max | `DeviceRS20ProPlus` | 2.0.1 |
| RS20 Hair Free | `DeviceRS20ProPlus` | 2.0.1 |
| RS20 Pro | `DeviceRS20Pro` | 2.0.0 |
| RE7 Edge | `DeviceRE7P` | 2.0.0 |
| RE3 Plus | `DeviceRE3P` | not offered by the EU server |
| RS2, RE4, RE5 and anything else | `DeviceSweepingRobot2` | 2.0.1 |
| RS2 manufacturer variant | `DeviceRS2ODM` | 2.0.1 |

The app treats RE3 Plus, RE4, RE4P, RE5 and RE5P as OEM devices. "RS20 Hair
Free" exists as a sub-category in the app, but no product of that name could be
found for sale.

## Commands compared with the RS20 Max

| Plugin | Differences that matter to the integration |
|---|---|
| `DeviceRS20Pro` | None in the commands used; no smart dirt detection setting. |
| `DeviceSweepingRobot2` | Same `CleanControl`, `RechargeControl`, `StartRegionClean` and `Set*OfStdClean` actions. No base-station settings (dust, detergent, mop washing), no `RestPlan` (uses `SweeperMgr/DayNightRestMode`), no carpet extras. |
| `DeviceRE7P` | Same `CleanControl` and `RechargeControl`. Suction and water use `SweeperMapMgr/SetCleanFanMode` and `SetCleanWaterQuantity` with `{mapID, cfgType, regionID, fanMode/waterQuantity}`, plus `SetGlobalCleanCfg` and `SetCleanModeType`. No mop washing, dust or detergent settings. |
| `DeviceRS2ODM` | Start/pause/resume/stop is `SweeperCleanTask/CleanCtrl` (same string values). Docking is `SweeperTaskMgr/RechargeCtrl` with `{action: "start", source: "mobile"}`. No carpet, dust, detergent, mop washing or do-not-disturb settings. |

All plugins read the map through the same `/v3/sweeprobot/v3/rule/*` endpoints.

## How the plugins were fetched

`POST /nodeupdate/v9/rn/check` on the account's API host, with headers
`appId: a47d2e41dd804038940407b22fe61726`, `clientType: 3` and
`clientVersion: 7.6.3.2874525`, and a body listing the plugin ids:

```json
{"prefixP": "", "prefixE": "", "region": "", "productLine": "ez",
 "bids": [{"bid": "DeviceRS20Pro", "version": "7.0.0.1",
           "builtInVersion": "7.0.0.1", "pubVersion": "7.0.0.30000013"}]}
```

Each answer contains a download URL and an MD5 of the zip. The commands were
extracted from the `sendAction`, `readFeature` and `writeFeature` calls in each
bundle.
