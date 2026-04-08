# AutoStore Warehouse Safety Procedures

## General Safety Rules

1. **Never walk on the grid** while robots are operational. The grid surface is not designed for foot traffic, and active robots cannot detect humans on the grid.
2. **Always use the lockout/tagout (LOTO) procedure** before entering the grid area for maintenance.
3. **Wear required PPE** when working near the grid: safety shoes, high-visibility vest, and safety glasses.
4. **Report all incidents** through the warehouse management system within 1 hour of occurrence.
5. **Know your emergency stop locations.** Each workstation has an E-STOP button. Additional E-STOPs are located at grid access points.

## Lockout/Tagout Procedure for Grid Access

### Before Entering the Grid Area

1. Notify the shift supervisor of planned grid access
2. Use the Controller to create a safety zone: `POST /safety/zone/create` with the grid coordinates
3. The system will route all robots away from the defined zone
4. Wait for confirmation that the zone is clear (green indicator on the Controller dashboard)
5. Apply a physical lock to the grid access gate
6. Attach your personal tag to the lock
7. Verify no robots are in the zone by visual inspection

### While Working on the Grid

- Stay within the defined safety zone
- Keep radio contact with the control room at all times
- Do not remove or displace bins without Controller approval
- If you hear a robot approaching, stop work and contact the control room immediately
- Maximum grid access duration: 2 hours (renewable with supervisor approval)

### After Completing Grid Work

1. Remove all tools and materials from the grid
2. Exit through the grid access gate
3. Remove your personal tag and lock
4. Notify the control room: `POST /safety/zone/{zone_id}/release`
5. The Controller will reopen the zone for robot traffic

## Fire Safety

### Prevention
- No open flames within 10 meters of the grid
- Lithium-ion battery storage area must have Class D fire extinguishers
- Charging stations equipped with automatic fire suppression
- Monthly fire extinguisher inspection required

### If a Fire Occurs
1. Activate the fire alarm
2. Execute system emergency stop: `POST /system/estop`
3. Evacuate all personnel via designated exit routes
4. Do NOT attempt to fight a lithium battery fire with water
5. Use the CO2 or Class D extinguisher for battery fires
6. Assembly point: parking lot area A (northeast corner)

## Working at Height

Grid maintenance sometimes requires working at elevated positions (the grid is typically 5-6 meters above warehouse floor).

### Requirements
- Fall protection harness required above 2 meters
- Scaffold or mobile elevating work platform (MEWP) for grid-level access
- Two-person minimum for any work at height
- Wind speed must be below 40 km/h for outdoor sections

## Robot Interaction Safety

### Normal Operations
- Robots have right-of-way on the grid at all times
- Never reach into a port while a robot is delivering a bin
- Wait for the "bin ready" indicator (green light) before accessing a bin at a workstation
- If a bin appears unstable, press the port E-STOP before reaching in

### Emergency Robot Stop
If a robot exhibits dangerous behavior (erratic movement, sparks, smoke):
1. Press the nearest E-STOP button
2. If safe to do so, note the robot ID (printed on the side panel)
3. Report immediately to the control room
4. Do not attempt to physically stop or redirect a moving robot

## Incident Reporting

All safety incidents must be recorded in the warehouse management system:
- **Near miss:** Report within the same shift
- **Minor incident (no injury):** Report within 1 hour
- **Injury incident:** Report immediately, seek first aid
- **Major incident:** Call emergency services, evacuate area, report to site manager

### Incident Report Fields
- Date, time, and location (grid coordinates if applicable)
- People involved
- Description of what happened
- Immediate actions taken
- Root cause (if known)
- Corrective actions proposed
