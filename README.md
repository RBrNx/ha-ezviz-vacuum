# EZVIZ RS20 for Home Assistant

An unofficial Home Assistant custom integration for **EZVIZ RS20** robot
vacuums and their base stations. Developed and tested with an RS20 Max
(`CS-RS20-MAX-TGA`, firmware V2.0.2417); the RS20 Pro and other EZVIZ robots
that use the same cloud protocol are detected as well.

This is a fork of
[Dmgerr/home-assistant-ezviz-rs20-pro](https://github.com/Dmgerr/home-assistant-ezviz-rs20-pro).
The integration domain is still `ezviz_rs20pro`, so it replaces the original
without losing entities.

> EZVIZ does not publish an API for its robots. The integration uses the cloud
> endpoints of the EZVIZ app, so firmware or cloud changes can break features.
> The robot cannot be controlled locally.

## Features

**Vacuum**
- Start, pause, stop and return to the dock, with the state taken from the
  robot's live task (cleaning, paused, returning, docked, error).
- Suction level (Quiet, Normal, Strong, Max) from the vacuum entity.
- Room cleaning through Home Assistant areas, using the robot's active map and
  the selected cleaning mode.
- Robot errors in English, with the error code.

**Settings**
- Cleaning mode (vacuum only, mop only, vacuum and mop, vacuum then mop),
  water level and cleaning passes.
- Per-room suction, water level and passes, and the switch between the same
  settings for every room and per-room settings.
- Do not disturb with start and end times, and whether cleaning resumes.
- Schedules made in the app: turn them on or off and change the start time.
- Carpet detection, suction boost, extra cleaning and crossing carpets.
- Mop washing (after an interval or after each room), wash interval and drying
  time; how often the station empties the dust bin.
- Pet mode, smart dirt detection, debris boost,
  deep edge cleaning, voice assistant, voice volume and off-peak charging.
- Station child lock, automatic dust collection, cleaning-solution dosing and
  rotating-brush self-cleaning.

Cliff detection is deliberately not exposed.

**Sensors**
- Battery, Wi-Fi signal, current task, task duration, on base station and do
  not disturb active.
- Consumables in percent, with hours left and used: main brush, side brush,
  HEPA filter, mop pads, dust bag, sensors, dirty water tank filter and
  cleaning solution.
- Lifetime totals: cleaned area, cleaning time, cleanings, dust collections,
  mop washes and battery charge cycles.
- Last error and last cleaning run (area, duration, mode, how it started and
  why it stopped), from the robot's own history.
- Base-station status: mop washing, mop drying, dust collection and tank
  draining.

**Other**
- Several robots on one Home Assistant; every service takes an optional serial.
- An on-demand robot camera snapshot (see below).
- Admin-only raw request services for protocol discovery.
- Interface in English, German, Spanish, French, Italian and Polish.

Rooms and schedules are read when the integration starts. Reload it after
editing the map or adding a schedule in the app.

## Requirements

- Home Assistant 2026.7 or newer.
- The robot added to the EZVIZ app.
- The official **EZVIZ** integration configured and loaded. This integration
  reuses its session and does not store your EZVIZ credentials.

## Install with HACS

1. In HACS, open the three-dot menu and choose **Custom repositories**.
2. Add `https://github.com/stefanelul2000/ha-ezviz-rs20` as an
   **Integration**.
3. Download **EZVIZ RS20** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and choose
   **EZVIZ RS20**. If the account has several robots, pick one and repeat for
   the others.

To switch from the original repository, remove it from HACS, add this one and
download it; existing entities are kept.

## Polling

The live task is read every 30 seconds. The full device report, which
includes settings, consumables and history, is read every 5 minutes and
whenever the robot starts a different task. Changed settings show up
immediately.

## Camera privacy

The image entity holds only the latest snapshot in memory. The camera opens
for a few seconds only when `ezviz_rs20pro.refresh_camera_snapshot` is called.
Nothing is recorded or written to disk.

## Troubleshooting

- If setup says EZVIZ is missing, configure or reload the official EZVIZ
  integration first.
- Restart Home Assistant after updating so new platforms load.
- When reporting a problem, include the Home Assistant version, robot model
  and firmware, and the output of the **Inspect robot** service. It removes
  credentials, but check it before posting.

## Development

```bash
python -m unittest discover -s tests -t tests -v
```

HACS validation, Hassfest and the tests run on GitHub.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). This project is not
affiliated with or endorsed by EZVIZ. Use it at your own risk.
