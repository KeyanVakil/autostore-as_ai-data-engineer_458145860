# AutoStore Controller API Reference

## Overview

The AutoStore Controller exposes a REST API for monitoring and managing the warehouse system. All endpoints require authentication via API key (header: `X-AS-API-Key`). The API runs on the Controller hardware, typically accessible at `https://controller.local:8443`.

## Base URL

```
https://{controller-host}:8443/api/v2
```

## Authentication

All requests must include the API key header:
```
X-AS-API-Key: {your-api-key}
```

## Robot Management

### List All Robots
```
GET /robots
```

Response:
```json
{
  "robots": [
    {
      "robot_id": "R5-117",
      "status": "active",
      "battery_level": 78,
      "position": {"x": 14, "y": 23},
      "current_task": "retrieval",
      "firmware_version": "5.3.1",
      "uptime_hours": 2847
    }
  ],
  "total": 45,
  "active": 42,
  "charging": 2,
  "maintenance": 1
}
```

### Get Robot Details
```
GET /robots/{robot_id}
```

### Send Robot to Maintenance Port
```
POST /robots/{robot_id}/maintenance
```
Body: `{"reason": "scheduled_maintenance", "port": "M1"}`

### Run Robot Diagnostic
```
POST /robots/{robot_id}/diagnostic
```
Body: `{"type": "full" | "battery" | "wheels" | "gripper" | "sensors"}`

Response includes test results for each subsystem.

### Shutdown Robot
```
POST /robots/{robot_id}/shutdown
```

### Restart Robot
```
POST /robots/{robot_id}/restart
```

## Grid Management

### Get Grid Status Overview
```
GET /grid/status
```

Response:
```json
{
  "dimensions": {"x": 80, "y": 120},
  "total_cells": 9600,
  "obstructed_cells": 3,
  "total_bin_positions": 153600,
  "occupied_positions": 98432,
  "fill_rate": 0.641,
  "temperature_avg": 22.3,
  "temperature_max": 27.1
}
```

### Get Cell Details
```
GET /grid/cell/{x}/{y}
```

Response:
```json
{
  "position": {"x": 14, "y": 23},
  "status": "normal",
  "column_depth": 16,
  "bins_stored": 12,
  "top_bin_id": "BIN-004523",
  "robots_nearby": ["R5-117"],
  "last_access": "2025-03-12T14:23:00Z"
}
```

### Reset Cell Status
```
POST /grid/cell/{x}/{y}/reset
```

### Get Column Inventory
```
GET /grid/column/{x}/{y}/bins
```

Response: ordered list of bins from top (depth 0) to bottom.

### Run Column Audit
```
POST /grid/column/{x}/{y}/audit
```

Triggers a physical audit where a robot verifies each bin in the column against the database.

## Port Management

### List All Ports
```
GET /ports
```

### Get Port Status
```
GET /ports/{port_id}/status
```

Response:
```json
{
  "port_id": "P1",
  "type": "picking",
  "status": "active",
  "current_bin": "BIN-004523",
  "queue_depth": 3,
  "throughput_today": 487,
  "operator": "operator-12"
}
```

### Emergency Stop Port
```
POST /ports/{port_id}/estop
```

### Reset Port
```
POST /ports/{port_id}/reset
```

## System Operations

### System Health
```
GET /system/health
```

Response:
```json
{
  "status": "healthy",
  "controller_version": "4.2.3",
  "uptime_hours": 8760,
  "robot_fleet_health": 0.93,
  "grid_utilization": 0.64,
  "active_tasks": 127,
  "alerts": []
}
```

### Emergency Stop (All)
```
POST /system/estop
```

Halts all robots and ports immediately.

### Clear Emergency Stop
```
POST /system/estop/clear
```
Body: `{"supervisor_pin": "****"}`

### Resume Operations
```
POST /system/resume
```
Body: `{"mode": "gradual" | "immediate"}`

Gradual mode brings robots online in batches of 10 over 5 minutes.

## Task Management

### List Active Tasks
```
GET /tasks
```

### Get Task Details
```
GET /tasks/{task_id}
```

### Cancel Task
```
POST /tasks/{task_id}/cancel
```

### Get Task Statistics
```
GET /tasks/stats
```

Response:
```json
{
  "period": "today",
  "total_tasks": 4523,
  "completed": 4198,
  "in_progress": 127,
  "cancelled": 45,
  "failed": 23,
  "average_completion_time_seconds": 34.2,
  "throughput_per_hour": 520
}
```

## Safety Zones

### Create Safety Zone
```
POST /safety/zone/create
```
Body:
```json
{
  "x_start": 10,
  "y_start": 15,
  "x_end": 14,
  "y_end": 19,
  "reason": "maintenance",
  "operator": "tech-07",
  "duration_minutes": 120
}
```

### Release Safety Zone
```
POST /safety/zone/{zone_id}/release
```

### List Active Safety Zones
```
GET /safety/zones
```

## Configuration

### Get System Config
```
GET /system/config
```

### Update Config Parameter
```
PUT /system/config/{parameter}
```
Body: `{"value": <new_value>}`

Common configurable parameters:
- `temp-threshold`: Temperature warning threshold (default: 35°C)
- `max-robot-speed`: Maximum robot speed in cells/second (default: 4)
- `reservation-lookahead`: Number of cells robots reserve ahead (default: 3)
- `auto-charge-threshold`: Battery level triggering auto-charge (default: 20%)
