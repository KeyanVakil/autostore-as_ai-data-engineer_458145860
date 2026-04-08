# AutoStore R5+ Robot Maintenance Guide

## Overview

The R5+ is AutoStore's fifth-generation grid robot, designed for high-throughput warehouse operations. Each robot operates on top of the aluminum grid, retrieving and delivering bins to workstation ports. Regular maintenance ensures optimal uptime and extends the robot's operational lifespan.

## Scheduled Maintenance Intervals

### Daily Checks (Operator)
- Verify all status LEDs are green during startup sequence
- Listen for unusual motor sounds during grid traversal
- Check that the robot docks correctly at charging stations
- Report any visible damage to wheels or gripper mechanism

### Weekly Maintenance (Technician)
- Inspect wheel treads for wear; replace if tread depth < 2mm
- Clean the gripper suction cups with isopropyl alcohol
- Check belt tension on the lift mechanism (deflection should be 5-8mm)
- Verify IR sensors are free of dust and debris
- Run the built-in diagnostic cycle via the Controller API

### Monthly Maintenance (Engineer)
- Replace gripper suction cups (part number AS-R5-SUC-04)
- Lubricate wheel bearings with AutoStore-approved grease (AS-LUB-02)
- Inspect and clean electrical connectors on the charging interface
- Update firmware if a new version is available via the Controller
- Perform a full battery health check using the diagnostic tool

## Battery System

The R5+ uses a 48V lithium-ion battery pack (capacity: 2.4 kWh).

### Battery Specifications
- Nominal voltage: 48V DC
- Capacity: 50 Ah (2.4 kWh)
- Charging time: 45 minutes (10% to 90%)
- Expected lifespan: 3,000 charge cycles
- Operating temperature range: 5°C to 40°C

### Battery Replacement Procedure
1. Navigate the robot to a designated maintenance port
2. Power down the robot using the Controller API command: `POST /robot/{id}/shutdown`
3. Wait for all status LEDs to turn off (approximately 30 seconds)
4. Release the battery latch (orange lever on the underside)
5. Slide the battery pack out along the guide rails
6. Insert the replacement battery until the latch clicks
7. Power on and verify the battery reports > 50% charge
8. Run a short diagnostic: `POST /robot/{id}/diagnostic?type=battery`

### Battery Safety
- Never short-circuit battery terminals
- Store replacement batteries at 40-60% charge in a cool, dry location
- Dispose of depleted batteries through AutoStore's recycling program
- If a battery shows signs of swelling, isolate immediately and contact AutoStore support

## Wheel Replacement

### When to Replace
- Tread depth below 2mm (use the included gauge tool)
- Visible flat spots from prolonged stationary operation
- Excessive vibration during traversal reported by the Controller

### Procedure
1. Dock the robot at the maintenance port
2. Engage the wheel lock: `POST /robot/{id}/lock-wheels`
3. Use the 6mm hex wrench to remove the 4 mounting bolts per wheel
4. Slide the old wheel off the axle
5. Install the new wheel (part: AS-R5-WHL-06), torque bolts to 8 Nm
6. Release wheel lock and run the calibration routine
7. Verify smooth traversal across 10 grid cells in each direction

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Robot stops mid-grid | Obstacle detection triggered | Check for debris on grid rail, clear and restart |
| Slow bin retrieval | Gripper suction cups worn | Replace suction cups |
| Won't charge | Dirty charging contacts | Clean contacts with contact cleaner |
| Erratic movement | Wheel flat spot | Replace affected wheel |
| Red LED flashing 3x | Motor driver fault | Run diagnostic, may need board replacement |
| Red LED flashing 5x | Communication loss | Check grid antenna, restart Controller |
