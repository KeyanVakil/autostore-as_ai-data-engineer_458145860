# Grid System Troubleshooting Guide

## Grid Architecture Overview

The AutoStore grid consists of aluminum rail tracks arranged in a rectangular pattern. Robots travel on top of the grid, and bins are stacked in columns beneath the grid cells. Each grid cell is identified by its X-Y coordinate (e.g., cell [14, 23]).

### Grid Components
- **Top rails:** Aluminum T-profile rails where robots travel
- **Vertical columns:** Support structure holding the grid at the correct height
- **Bin columns:** Stack positions beneath each grid cell (up to 16 bins deep)
- **Ports:** Openings in the grid where bins are presented to operators

## Common Grid Issues

### Issue: Robot Cannot Traverse Specific Cell

**Symptoms:**
- Robot routes around a specific grid cell
- Controller logs show "cell blocked" warnings for that coordinate
- Multiple robots avoid the same area

**Diagnosis:**
1. Check the Controller grid map: `GET /grid/status?x={x}&y={y}`
2. If the cell shows "obstructed," perform a physical inspection
3. Look for:
   - Rail misalignment (gap > 1mm between rail joints)
   - Debris on the rail surface (packaging material, dust buildup)
   - A bin that has risen above the grid surface

**Resolution:**
- Clear any debris from the rail surface
- If rails are misaligned, loosen the mounting bolts and realign using the rail gauge tool (AS-TOOL-RG-01)
- If a bin is stuck above the surface, use the manual bin extractor to push it down
- Reset the cell status: `POST /grid/cell/{x}/{y}/reset`

### Issue: Bin Stuck in Column

**Symptoms:**
- Robot attempts retrieval but reports "bin not lifted"
- Repeated retrieval failures at the same column
- Adjacent columns may also be affected if the stuck bin is tilted

**Diagnosis:**
1. Query the bin position: `GET /grid/column/{x}/{y}/bins`
2. Check if the bin at the target depth matches the expected ID
3. Use the column camera (if installed) to inspect visually

**Resolution:**
1. Clear the column from above using the manual extractor tool
2. If the bin is tilted, carefully straighten it before extraction
3. Inspect the column walls for damage or obstructions
4. After clearing, run a column inventory audit: `POST /grid/column/{x}/{y}/audit`
5. If the bin is damaged, replace it with a new bin of the same size class

### Issue: Port Mechanism Jammed

**Symptoms:**
- Bins cannot be presented to operators at workstation ports
- Port status shows "fault" in the Controller dashboard
- Mechanical grinding noise from the port mechanism

**Diagnosis:**
1. Check port status: `GET /ports/{port_id}/status`
2. Inspect the conveyor belts and lift mechanism
3. Look for jammed or misaligned bins on the port conveyor

**Resolution:**
1. Emergency stop the port: `POST /ports/{port_id}/estop`
2. Manually remove any jammed bins
3. Inspect conveyor belts for damage; replace if torn
4. Reset the port: `POST /ports/{port_id}/reset`
5. Run the port calibration sequence before resuming operations

### Issue: Grid Temperature Warning

**Symptoms:**
- Controller dashboard shows temperature warnings
- Robots may automatically reduce speed
- In extreme cases, robots will park and wait for cooling

**Diagnosis:**
- Check ambient temperature: should be between 2°C and 35°C
- Verify HVAC system is operational
- Check if specific grid zones are hotter (near loading docks, skylights)

**Resolution:**
- Ensure warehouse HVAC maintains temperature within operating range
- Consider adding ventilation in hot zones
- If temporary, the system will auto-recover when temperature drops
- Adjust the temperature threshold if appropriate: `PUT /system/config/temp-threshold`

## Grid Maintenance Schedule

| Task | Frequency | Responsible |
|------|-----------|-------------|
| Visual rail inspection | Weekly | Technician |
| Rail joint tightness check | Monthly | Engineer |
| Column depth audit (sample) | Monthly | System (automated) |
| Full grid inventory reconciliation | Quarterly | Engineer |
| Port mechanism lubrication | Monthly | Technician |
| Support column inspection | Annually | Structural engineer |

## Emergency Procedures

### Grid Emergency Stop
Press the red E-STOP button at any workstation or use: `POST /system/estop`

This will:
1. Halt all robot movement immediately
2. Lower any bins currently being carried
3. Lock all port mechanisms
4. Send an alert to the operations team

### Recovery After E-STOP
1. Identify and resolve the root cause
2. Clear the E-STOP: `POST /system/estop/clear` (requires supervisor PIN)
3. Run a system health check: `GET /system/health`
4. Resume operations gradually: `POST /system/resume?mode=gradual`
