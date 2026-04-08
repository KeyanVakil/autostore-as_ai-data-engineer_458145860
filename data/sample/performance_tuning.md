# AutoStore System Performance Tuning Guide

## Key Performance Metrics

### Throughput
- **Bins per hour (BPH):** Primary measure of system productivity
- Typical range: 350-650 BPH depending on system size and configuration
- Measured at ports: `GET /tasks/stats` provides real-time and historical throughput

### Retrieval Time
- **Average retrieval time:** Time from task creation to bin presentation at port
- Target: < 30 seconds for top-4 depth, < 120 seconds for full-depth retrieval
- Factors: bin depth, robot availability, grid congestion, port queue depth

### Robot Utilization
- **Active time ratio:** Percentage of time robots are executing tasks vs. idle/charging
- Target: 70-85% during peak hours
- Below 70%: over-provisioned fleet or insufficient order volume
- Above 85%: risk of charging bottlenecks and increased wear

## Optimization Strategies

### 1. Bin Position Optimization (Heat Mapping)

The Controller maintains a "heat map" of SKU pick frequency. High-frequency items should be stored near the grid surface (depth 1-4) for fastest retrieval.

**Configuration:**
```
PUT /system/config/heat-map-rebalance
{
  "enabled": true,
  "rebalance_window": "02:00-05:00",
  "max_moves_per_night": 500,
  "min_pick_frequency_threshold": 10
}
```

**How it works:**
- During low-activity hours, robots rearrange bins to place high-frequency items at shallow depths
- Items with > 10 picks/day move toward depth 1-2
- Items with < 1 pick/week move toward depth 12-16
- Maximum 500 moves per night to limit robot wear

### 2. Robot Fleet Sizing

**Formula for minimum robots:**
```
robots_needed = (target_BPH * avg_retrieval_time_seconds) / 3600 * safety_factor
```

Where `safety_factor` = 1.3 (accounts for charging and maintenance).

**Example:**
- Target: 500 BPH
- Average retrieval time: 45 seconds
- Robots needed: (500 * 45) / 3600 * 1.3 = 8.1 -> minimum 9 robots

**Charging consideration:** At any given time, approximately 15% of the fleet will be charging. Size the fleet to meet target throughput with 85% availability.

### 3. Port Configuration

**Port types and throughput:**
| Port Type | Typical Throughput | Best For |
|-----------|-------------------|----------|
| Single-position | 100-150 BPH | Small installations |
| Carousel (3-position) | 200-300 BPH | High-volume picking |
| Relay port | 150-200 BPH | Cross-docking |
| Replenishment port | 80-120 BPH | Inbound operations |

**Optimization tips:**
- Place high-throughput ports near the center of the grid to minimize travel distance
- Dedicate ports during peak hours (no mixed picking/replenishment)
- Balance port queues: `GET /ports` shows queue depth for each port

### 4. Grid Layout Optimization

**Zone strategy:**
- Divide the grid into zones based on product category or pick frequency
- Fast-moving items in a zone closest to picking ports
- Slow-moving items in a zone furthest from ports
- Configure zone boundaries: `PUT /grid/zones`

**Corridor planning:**
- Maintain at least 2-cell-wide corridors for bidirectional traffic
- Avoid single-cell bottlenecks (major cause of congestion)
- The Controller's routing algorithm works best with multiple path options

### 5. Charging Station Placement

**Rules of thumb:**
- 1 charging station per 3-4 robots
- Distribute stations across the grid, not clustered in one corner
- Place stations near grid edges to keep the center clear for traffic
- Configure charge thresholds:

```
PUT /system/config/auto-charge-threshold
{"value": 20}

PUT /system/config/charge-complete-threshold
{"value": 90}
```

Robots auto-dock at 20% and return to service at 90%. Do not charge to 100% — it wastes time with minimal capacity gain and reduces battery lifespan.

## Monitoring and Alerting

### Key Metrics to Watch

| Metric | Warning Threshold | Critical Threshold |
|--------|------------------|--------------------|
| Throughput drop | > 15% below target | > 30% below target |
| Average retrieval time | > 60 seconds | > 120 seconds |
| Robot utilization | > 90% | > 95% |
| Charging queue | > 3 robots waiting | > 5 robots waiting |
| Port queue depth | > 5 bins | > 10 bins |
| Grid temperature | > 30°C | > 35°C |

### Setting Up Alerts
```
POST /alerts/rules
{
  "metric": "throughput_bph",
  "condition": "below",
  "threshold": 400,
  "duration_minutes": 15,
  "notification": ["email:ops-team@company.com", "sms:+47-XXX"]
}
```

## Seasonal Planning

### Peak Season Preparation (4-6 weeks before)
1. Perform full robot fleet maintenance
2. Run heat map optimization with updated pick frequency data
3. Increase the nightly rebalance move limit
4. Pre-position additional robots from standby fleet
5. Schedule extra technician coverage
6. Verify backup Controller is ready for failover

### Post-Peak Optimization
1. Analyze performance data from peak period
2. Identify bottleneck grid zones and consider layout changes
3. Return standby robots to maintenance cycle
4. Update pick frequency models with new data
5. Schedule deferred maintenance items

## Troubleshooting Performance Issues

### Sudden Throughput Drop
1. Check `GET /system/health` for alerts
2. Check robot fleet status: are multiple robots charging or in maintenance?
3. Check grid congestion: `GET /grid/congestion-map`
4. Check port status: is a port offline?
5. Check recent changes: firmware update, configuration change?

### Gradually Declining Performance
1. Review bin heat map: has it become stale? Run a rebalance.
2. Check robot wear: worn wheels reduce speed
3. Check grid condition: dirty rails slow robots
4. Review throughput trends: `GET /tasks/stats?period=30d`
5. Compare current robot count vs. order volume growth
