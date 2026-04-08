# AutoStore System Installation Checklist

**Document ID:** WH-DOC-IC-001
**Version:** 3.2
**Last Updated:** 2025-02-01

## Pre-Installation Requirements

### Site Preparation
- [ ] Floor load capacity verified: minimum 500 kg/m2 for grid area
- [ ] Floor flatness verified: maximum deviation 5mm over 3 meters
- [ ] Ceiling height confirmed: minimum grid height + 2 meters clearance
- [ ] Ambient temperature: HVAC maintains 5-35°C year-round
- [ ] Humidity: 20-80% non-condensing
- [ ] Fire suppression system installed and certified
- [ ] Emergency lighting in grid area
- [ ] E-STOP buttons installed at all workstation positions

### Electrical
- [ ] Main power supply: 400V 3-phase, minimum 200A for a 50-robot system
- [ ] UPS system for Controller and network equipment
- [ ] Dedicated circuit breakers for charging stations
- [ ] Grounding system verified by certified electrician
- [ ] Lightning protection for the building

### Network
- [ ] Dedicated VLAN for AutoStore components
- [ ] Wireless access points: minimum -65 dBm coverage across entire grid
- [ ] Controller network port: Gigabit Ethernet
- [ ] Firewall rules configured per AutoStore network specification
- [ ] NTP server accessible for time synchronization

## Grid Assembly

### Phase 1: Support Structure
- [ ] Column base plates anchored to floor per structural plan
- [ ] Vertical columns installed and plumbed (tolerance: 2mm vertical over full height)
- [ ] Cross-bracing installed per structural calculations
- [ ] Column heights verified with laser level

### Phase 2: Rail Installation
- [ ] Bottom rails installed and leveled
- [ ] Top rails installed with correct spacing (649mm center-to-center)
- [ ] Rail joints checked: gap < 0.5mm, height difference < 0.3mm
- [ ] Rail alignment verified with the AutoStore rail gauge
- [ ] All rail mounting bolts torqued to specification

### Phase 3: Port Installation
- [ ] Port openings cut in grid per layout drawing
- [ ] Port mechanisms mounted and aligned
- [ ] Conveyor belts installed and tensioned
- [ ] Port sensors calibrated
- [ ] Each port tested with a dummy bin: smooth delivery and return

## System Configuration

### Controller Setup
- [ ] Controller hardware rack-mounted in server room
- [ ] Operating system installed (AutoStore Controller OS)
- [ ] Network configured: static IP, DNS, NTP
- [ ] Grid dimensions programmed: X=__, Y=__, depth=__
- [ ] Port locations registered
- [ ] Charging station locations registered
- [ ] API keys generated for external integrations
- [ ] Backup schedule configured (daily incremental, weekly full)

### Robot Commissioning
For each robot:
- [ ] Unbox and physical inspection
- [ ] Firmware verified/updated to latest version
- [ ] Battery installed and initial charge to 100%
- [ ] Place on grid at designated starting position
- [ ] Register in Controller: `POST /robots/register`
- [ ] Run full diagnostic: `POST /robots/{id}/diagnostic?type=full`
- [ ] Test grid traversal: minimum 50 cells in each direction
- [ ] Test bin retrieval: pick up and return a bin from depth 1, 8, and 16
- [ ] Verify charging: dock at charging station, confirm charge current

### Software Integration
- [ ] WMS integration configured and tested
- [ ] Barcode scanner integration at each workstation
- [ ] Pick-to-light system configured (if applicable)
- [ ] Real-time dashboard access verified
- [ ] Alert notification system configured (email/SMS)
- [ ] API access tested from external systems

## Acceptance Testing

### Functional Tests
- [ ] Single robot retrieval from depth 1, 8, and 16 — all successful
- [ ] Multi-robot simultaneous operation — no collisions
- [ ] Port-to-port bin transfer — bin arrives undamaged
- [ ] Emergency stop — all robots halt within 1 second
- [ ] E-STOP recovery — system resumes cleanly
- [ ] Power loss recovery — system restarts and resumes after power cycle
- [ ] Full bin column — robot correctly reports "column full"

### Performance Tests
- [ ] Throughput test: target ___ bins/hour achieved with ___% of robots active
- [ ] Average retrieval time: < ___ seconds from request to port presentation
- [ ] Robot uptime: > 95% over 48-hour continuous test
- [ ] System recovery time: < 5 minutes after simulated Controller restart

### Safety Tests
- [ ] Safety zone creation and robot exclusion verified
- [ ] All E-STOP buttons tested (every station, every grid access point)
- [ ] Fire suppression interface tested (system shuts down on fire alarm)
- [ ] Temperature alarm triggers at configured threshold
- [ ] Collision avoidance: robots stop when approaching each other

## Training

### Operator Training (4 hours)
- [ ] Workstation operation: picking, replenishment, returns
- [ ] Bin handling procedures
- [ ] E-STOP usage
- [ ] Basic troubleshooting (what to report, who to call)
- [ ] Safety procedures specific to AutoStore

### Technician Training (2 days)
- [ ] Robot maintenance procedures
- [ ] Grid inspection and minor repairs
- [ ] Port mechanism maintenance
- [ ] Controller dashboard operation
- [ ] Diagnostic tools usage
- [ ] Incident reporting

### Engineer Training (3 days)
- [ ] Controller API usage
- [ ] System configuration and tuning
- [ ] Performance optimization
- [ ] Advanced troubleshooting
- [ ] Firmware update procedures
- [ ] Integration management

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AutoStore Project Manager | | | |
| Customer Project Manager | | | |
| Site Safety Officer | | | |
| IT Manager | | | |
