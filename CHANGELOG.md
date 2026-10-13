# Changelog

## 0.7.0

- Live map: a new **Map** image entity draws the active map with coloured,
  named rooms, walls, obstacles, the dock, the robot and the path of the
  current clean. Layers are downloaded only when they change, and the path is
  cleared once the robot is docked.
- The live task is polled every 10 seconds while the robot cleans or returns.
- Suction, water level, passes and room settings are now changed the way the
  EZVIZ app does it, so they take effect immediately, even mid-clean. Room
  cleaning no longer overrides them with each room's stored values.
- A paused clean shows as paused, and starting it again resumes it instead of
  being refused.
- Return to dock uses the robot's recharge command and works again.
- Refusals from the robot are explained in English.
- The raw API request service can send JSON bodies and headers.
- Removed the enhanced obstacle recognition and voice assistant switches,
  which the robot does not accept from Home Assistant.
- README rewritten.

## 0.6.0

First release of this fork, now named EZVIZ RS20.

- Settings: suction level on the vacuum, cleaning mode, water level, cleaning
  passes, per-room suction, water and passes, do not disturb, schedules,
  carpet options, mop washing and drying, dust collection frequency, feature
  switches, voice volume and off-peak charging.
- Sensors: lifetime totals, battery cycles, consumable hours, dirty water tank
  filter, current task, task duration, relocation failures, last error, last
  cleaning run and Wi-Fi signal; binary sensors for being on the base station
  and do not disturb.
- The vacuum state follows the robot's live task, and errors are described in
  English.
- Rooms and room cleaning use the robot's active map; room cleaning uses the
  selected cleaning mode.
- The device shows the real model and firmware; other EZVIZ robot vacuums are
  detected.
- Several robots can be added; services take an optional serial.
- Failed commands are reported as errors instead of failing silently.
- The full device report is polled every 5 minutes instead of every 30
  seconds.
- Admin-only raw request services for protocol discovery.
- All texts in English; translations updated for all six languages.
- Removed unused cloud replay and stream code.

## 0.5.1

- Add an original repository-local brand icon for HACS.
- Sort manifest keys according to Home Assistant validation requirements.

## 0.5.0

- Add base-station status sensors for mop washing, mop drying, dust collection,
  water-tank draining and the optional plumbing module.
- Add safe station setting switches for child lock, automatic dust collection,
  automatic cleaning-solution dosing and rotating-brush self-cleaning.
- Add English, Polish, German, French, Spanish and Italian translations.
- Add HACS packaging, documentation, tests and GitHub validation workflows.
- Keep the robot camera privacy-first: snapshots are captured only on request.

## 0.4.2

- Add native room cleaning, on-demand camera snapshots, maintenance sensors and
  diagnostics for the RS20 Pro cloud protocol.
