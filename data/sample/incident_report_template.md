# Incident Report: Robot Collision on Grid Section B

**Report ID:** IR-2025-0042
**Date of Incident:** 2025-03-12
**Time:** 14:23 UTC
**Location:** Grid Section B, Cell [34, 17]
**Severity:** Medium
**Status:** Resolved

## Summary

Two R5+ robots (Robot-117 and Robot-203) collided at grid cell [34, 17] during a high-throughput picking period. Robot-117 sustained minor wheel damage. Robot-203 was undamaged. No bins were dropped and no inventory was damaged. Total downtime: 47 minutes.

## Timeline of Events

| Time | Event |
|------|-------|
| 14:20 | Both robots assigned retrieval tasks in adjacent columns |
| 14:22 | Robot-117 rerouted due to congestion on its primary path |
| 14:23 | Robot-117 and Robot-203 arrived at cell [34, 17] simultaneously |
| 14:23 | Collision detected by both robots' proximity sensors |
| 14:23 | Both robots executed emergency stop |
| 14:25 | Control room alerted, operator dispatched |
| 14:35 | Technician arrived at grid section B |
| 14:42 | Robot-203 cleared — self-diagnostic passed |
| 14:55 | Robot-117 removed from grid — wheel damage identified |
| 15:10 | Grid section B cleared for normal operation |
| 15:45 | Robot-117 wheel replaced, returned to service after diagnostics |

## Root Cause Analysis

The Controller's traffic management system uses a reservation-based routing algorithm. Each robot reserves its next 3 grid cells. In this case:

1. Robot-117 was rerouted after its original path was blocked
2. The rerouting calculation and Robot-203's reservation were processed in the same scheduling tick
3. A race condition in the reservation system allowed both robots to reserve cell [34, 17]
4. The proximity sensors prevented a harder collision, but the robots still made contact at low speed

## Contributing Factors

- High system throughput (92% capacity) during the afternoon picking peak
- Grid section B has a narrow corridor (2 cells wide) that creates routing bottlenecks
- The firmware version on the Controller (v4.2.1) has a known timing issue in the reservation system

## Corrective Actions

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Update Controller firmware to v4.2.3 (fixes reservation race condition) | IT Team | 2025-03-15 | Completed |
| Add speed reduction zone in grid section B narrow corridor | Operations | 2025-03-13 | Completed |
| Review and widen routing options in section B | Engineering | 2025-04-01 | In Progress |
| Implement enhanced collision avoidance logging | IT Team | 2025-03-20 | Completed |

## Damage Assessment

- **Robot-117:** Right front wheel scuffed, replaced during the incident. Cost: 85 EUR (parts) + 0.75 hours labor
- **Robot-203:** No damage
- **Grid infrastructure:** No damage
- **Inventory:** No damage (no bins were being carried at the point of collision)

## Lessons Learned

1. The reservation system race condition was known but deprioritized. High-throughput periods expose edge cases in scheduling algorithms.
2. Narrow grid corridors should have mandatory speed limits. The current default speed was too high for the available reaction distance.
3. Proximity sensors worked as designed — without them, the collision would have been significantly worse.

## Recommendations

- Prioritize Controller firmware updates that address safety-related bugs
- Conduct a grid-wide review of narrow corridors and implement appropriate speed limits
- Add automated alerts when system throughput exceeds 85% capacity to warn operators
- Include collision scenario testing in the quarterly system validation schedule
