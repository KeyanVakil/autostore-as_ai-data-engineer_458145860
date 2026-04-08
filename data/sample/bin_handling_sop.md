# Standard Operating Procedure: Bin Handling

**SOP Number:** WH-SOP-004
**Effective Date:** 2025-01-15
**Review Date:** 2026-01-15
**Department:** Warehouse Operations

## Purpose

This SOP defines the procedures for handling, inspecting, and managing bins within the AutoStore system. Proper bin handling prevents inventory damage, reduces system downtime, and maintains retrieval efficiency.

## Scope

Applies to all warehouse operators, technicians, and supervisors who interact with AutoStore bins during picking, replenishment, returns processing, or maintenance.

## Bin Specifications

| Attribute | Standard Bin | Half-Height Bin | Quarter Bin |
|-----------|-------------|-----------------|-------------|
| Part Number | AS-BIN-330 | AS-BIN-220 | AS-BIN-110 |
| External Dimensions | 649 x 449 x 330mm | 649 x 449 x 220mm | 449 x 330 x 220mm |
| Maximum Load | 30 kg | 20 kg | 10 kg |
| Color Code | Gray | Blue | Green |
| Max Stack Depth | 16 | 16 | N/A (stored in standard bins) |

## Picking Operations

### Receiving a Bin at the Workstation

1. Wait for the port indicator light to turn green
2. Verify the bin ID displayed on the workstation screen matches the physical bin label
3. If the bin ID does not match, press "Bin Mismatch" on the workstation terminal and do NOT remove items
4. Pick the required items as shown on the pick list
5. Confirm the pick on the workstation terminal
6. The bin will automatically return to the grid

### Handling Guidelines
- Never exceed the maximum bin load weight
- Place heavy items at the bottom of the bin
- Use dividers for small items to prevent shifting during transport
- Do not stack items above the bin rim — this causes jams during stacking
- Handle bins by the reinforced rim edges, not the sides

## Replenishment

### Adding Inventory to Bins

1. Request a bin at the replenishment port: scan the SKU barcode
2. The system will deliver the appropriate bin (or an empty bin for new SKUs)
3. Place items in the bin according to the storage layout shown on screen
4. Scan each item as it's placed in the bin
5. Confirm replenishment complete on the terminal
6. The bin returns to the grid and the inventory system updates

### New SKU Setup
- New SKUs must be registered in the WMS before physical replenishment
- Assign the SKU to a bin size class (standard, half-height, or quarter)
- The system auto-assigns a grid column based on pick frequency predictions

## Bin Inspection

### When to Inspect
- During scheduled monthly quality checks
- When an operator reports a damaged bin
- After any grid incident involving stuck or fallen bins
- When the system flags a bin for inspection (automatic crack detection)

### Inspection Criteria

| Check | Pass | Fail |
|-------|------|------|
| Structural integrity | No cracks, no warping | Visible cracks, warped sides |
| Label readability | Barcode scans on first attempt | Barcode unreadable after 2 attempts |
| Rim condition | Smooth, no chips | Chipped or rough edges |
| Base flatness | Sits flat on inspection table | Rocks or has visible bowing |
| Cleanliness | No residue affecting items | Sticky residue, stains, mold |

### Failed Inspection
1. Remove the bin from service immediately
2. Transfer contents to a replacement bin
3. Record the failure in the bin tracking system
4. Damaged bins go to the recycling area — do not attempt to repair

## Bin Cleaning

### Routine Cleaning (Monthly)
- Wipe interior with a damp cloth and mild detergent
- Dry thoroughly before returning to service
- Do not use abrasive cleaners (damages bin surface)

### Deep Cleaning (As Needed)
- For bins contaminated with spills or chemicals
- Wash with warm water (< 60°C) and approved cleaning solution
- Air dry completely (minimum 4 hours)
- Re-inspect before returning to service

## Returns Processing

1. Operator receives returned items at the returns workstation
2. Inspect each item per the returns quality checklist
3. Scan the item to identify the home bin
4. Request the bin at the returns port
5. Place the item in the bin and confirm on the terminal
6. For damaged items, route to the quarantine bin (red label)

## Emergency Bin Handling

### Bin Fallen from Grid
1. Secure the area around the fallen bin
2. Report the incident to the shift supervisor
3. Check for inventory damage and document with photos
4. Investigate why the bin fell (misaligned column, robot malfunction)
5. Do NOT re-stack the bin without engineer approval

### Chemical Spill in Bin
1. Don appropriate PPE (gloves, goggles as specified on the MSDS)
2. Remove the bin from the grid system via the nearest port
3. Contain the spill using absorbent materials
4. Clean per the chemical's MSDS guidelines
5. The bin may need to be retired if contamination cannot be fully removed
