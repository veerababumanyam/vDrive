# Observability Tools Guide

Comprehensive guide to using vDrive's observability stack: Prometheus, Grafana, Loki, and Alertmanager.

## Overview

| Tool | URL | Purpose | Credentials |
|------|-----|---------|-------------|
| Grafana | http://localhost:3001 | Dashboards, visualization | admin/admin |
| Prometheus | http://localhost:9090 | Metrics collection, queries | none |
| Alertmanager | http://localhost:9094 | Alert management | none |
| Loki | http://localhost:3100 | Log aggregation | none (API only) |
| Traefik | http://localhost:8080 | Gateway dashboard | none |

## Grafana

### Accessing Grafana

```bash
# Open in browser
open http://localhost:3001

# Login: admin / admin
```

### Key Dashboards

**vDrive Services Overview**
- Service health (up/down)
- Request rate per second
- Error rate (5xx errors)
- P95 latency
- PostgreSQL connections
- Redis memory usage
- Kafka consumer lag

**Navigation:** Home → Dashboards → vDrive Services Overview

### Common Tasks

**View Service Metrics**
1. Navigate to dashboard
2. Select service from dropdown (top right)
3. Select time range (top right)
4. Panels update automatically

**Investigate Error Spike**
1. Locate "Error Rate (5xx)" panel
2. Note time of spike
3. Click panel title → View
4. Inspect raw data
5. Use time range to query logs in Loki

**Check P95 Latency**
1. Locate "P95 Latency by Service" panel
2. Identify slow service
3. Correlate with error rate
4. Check database/Redis metrics

**Export Dashboard**
1. Click Share icon (top right)
2. Export → Save to file
3. Attach to incident report

### Creating Custom Panels

```
1. Click "+ Add Panel"
2. Select data source: Prometheus
3. Enter PromQL query (see Prometheus section)
4. Configure visualization (Graph, Stat, Table)
5. Save dashboard
```

**Example Panel: Request Rate**
- Query: `rate(http_requests_total{job="backend"}[5m])`
- Visualization: Time series
- Legend: `{{method}} {{endpoint}}`

### Alerting

**View Active Alerts**
1. Navigate to Alerting → Alert rules
2. Filter by state (firing, pending, normal)
3. Click alert for details

**Create Alert Rule**
1. Navigate to dashboard panel
2. Click panel title → Edit
3. Alert tab → Create alert rule
4. Set condition (e.g., threshold)
5. Configure notification channel

## Prometheus

### Accessing Prometheus

```bash
# Open in browser
open http://localhost:9090

# Query API
curl 'http://localhost:9090/api/v1/query?query=up'
```

### Web UI

**Execute Query**
1. Navigate to Graph tab
2. Enter PromQL query
3. Click Execute
4. View Table or Graph

**View Targets**
1. Navigate to Status → Targets
2. Check scrape status (UP/DOWN)
3. Verify last scrape time
4. Check error messages

**View Alerts**
1. Navigate to Alerts
2. Filter by state (firing, pending, inactive)
3. Click alert for details

### PromQL Queries

```promql
# Service Health
up{job="backend"}                                      # Service up?
count(up{job=~"backend|onboarding-service"} == 1)      # Healthy count

# Request Metrics
rate(http_requests_total{job="backend"}[5m])           # RPS
rate(http_requests_total{status=~"5..", job="backend"}[5m])  # Error RPS
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100  # Error %

# Latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="backend"}[5m]))  # P95

# Database
pg_stat_activity_count                                 # Active connections
pg_stat_activity_count / pg_settings_max_connections * 100  # Pool usage %
rate(pg_stat_database_deadlocks{datname="vDrive"}[5m]) # Deadlocks

# Redis
redis_memory_used_bytes / redis_memory_max_bytes * 100 # Memory %
redis_connected_clients                                # Clients
rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100  # Hit ratio %

# Kafka
kafka_consumer_group_lag                               # Consumer lag
rate(kafka_topic_messages_in_per_sec[5m])              # Messages/sec
```

### API Usage

**Query Current Value**
```bash
# Single query
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=up{job="backend"}' | jq

# Multiple queries
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=rate(http_requests_total{job="backend"}[5m])' | jq
```

**Query Range**
```bash
# Query over time range
curl -G http://localhost:9090/api/v1/query_range \
  --data-urlencode 'query=rate(http_requests_total{job="backend"}[5m])' \
  --data-urlencode 'start=2026-01-14T10:00:00Z' \
  --data-urlencode 'end=2026-01-14T11:00:00Z' \
  --data-urlencode 'step=60s' | jq
```

**List Metrics**
```bash
# All metrics
curl http://localhost:9090/api/v1/label/__name__/values | jq

# Metrics for specific job
curl -G http://localhost:9090/api/v1/series \
  --data-urlencode 'match[]={job="backend"}' | jq
```

**Check Targets**
```bash
# List all scrape targets
curl http://localhost:9090/api/v1/targets | jq

# Filter by state
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'
```

## Loki (Log Aggregation)

### Accessing Loki

Loki has no web UI. Use Grafana's Explore or API.

**Via Grafana:**
1. Navigate to Explore (compass icon)
2. Select "Loki" data source
3. Enter LogQL query
4. Run query

**Via API:**
```bash
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="backend"}' | jq
```

### LogQL Queries

```logql
# Basic
{job="backend"}                                        # All logs
{job="backend", level="error"}                         # Error logs only
{job="backend"} |= "connection timeout"                # Filter message
{job="backend"} |~ "error|exception|failed"            # Regex filter

# JSON Parsing
{job="backend"} | json | level="error"                 # Parse + filter
{job="backend"} | json | user_id="user_123"            # By user
{job="backend"} | json | workspace_id="ws_001"         # By workspace

# Correlation Tracking
{job="backend"} | json | request_id="abc123"           # By request ID
{job=~"backend|onboarding-service"} | json | request_id="abc123"  # Cross-service trace

# Aggregations
rate({job="backend", level="error"}[5m])               # Error rate
count_over_time({job="backend"} |= "connection timeout" [30m])  # Count errors
topk(10, sum by (message) (count_over_time({job="backend", level="error"} | json [1h])))  # Top errors
```

### API Usage

**Instant Query**
```bash
# Query logs (last 5 minutes)
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="backend"}' \
  --data-urlencode 'limit=100' | jq

# Filter by level
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="backend", level="error"}' \
  --data-urlencode 'limit=50' | jq

# Search by request ID
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="backend"} | json | request_id="abc123"' | jq
```

**Range Query**
```bash
# Query over time range
curl -G http://localhost:3100/loki/api/v1/query_range \
  --data-urlencode 'query={job="backend", level="error"}' \
  --data-urlencode 'start=2026-01-14T10:00:00Z' \
  --data-urlencode 'end=2026-01-14T11:00:00Z' \
  --data-urlencode 'limit=100' | jq
```

**Label Values**
```bash
# List available jobs
curl http://localhost:3100/loki/api/v1/label/job/values | jq

# List available levels
curl http://localhost:3100/loki/api/v1/label/level/values | jq
```

**Tail Logs (Live Stream)**
```bash
# Stream logs in real-time
curl -G http://localhost:3100/loki/api/v1/tail \
  --data-urlencode 'query={job="backend"}' \
  --data-urlencode 'limit=10'
```

## Alertmanager

### Accessing Alertmanager

```bash
# Open in browser
open http://localhost:9094
```

### Viewing Alerts

**Active Alerts**
1. Navigate to Alerts page
2. View firing/pending alerts
3. Click alert for details (labels, annotations)

**Silences**
1. Navigate to Silences page
2. View active/expired silences
3. Create new silence

### Creating Silences

**Via Web UI:**
```
1. Navigate to Silences
2. Click "New Silence"
3. Add matchers (e.g., alertname="HighErrorRate")
4. Set duration (e.g., 2h)
5. Add comment
6. Create
```

**Via API:**
```bash
# Create silence
curl -X POST http://localhost:9094/api/v2/silences \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "HighErrorRate", "isRegex": false}
    ],
    "startsAt": "2026-01-14T10:00:00Z",
    "endsAt": "2026-01-14T12:00:00Z",
    "createdBy": "operator",
    "comment": "Investigating high error rate"
  }'

# List silences
curl http://localhost:9094/api/v2/silences | jq

# Delete silence
curl -X DELETE http://localhost:9094/api/v2/silence/[silence-id]
```

## Traefik Dashboard

### Accessing Traefik

```bash
# Open dashboard
open http://localhost:8080/dashboard/

# View metrics
curl http://localhost:8082/metrics
```

### Key Information

**HTTP Routers**
- Shows configured routes
- Backend services
- Middleware applied

**Services**
- Health of backend services
- Load balancing status

**Middleware**
- Rate limiting
- Authentication
- Headers

## Integration Workflows

### Error Spike Investigation
1. Detect in Grafana → note timestamp
2. Query Prometheus: `sum by (endpoint) (rate(http_requests_total{status=~"5.."}[5m]))`
3. Query Loki for errors in time range
4. Extract request_id from logs
5. Trace full request flow: `{job=~"backend|onboarding"} | json | request_id="abc123"`

### Performance Investigation
1. Check P95 latency in Grafana
2. Query DB metrics: `pg_stat_activity_count`
3. Find slow logs: `{job="backend"} | json | duration_seconds > 1`

### Health Check
1. Check targets: `curl http://localhost:9090/api/v1/targets | jq`
2. Verify uptime: `curl 'http://localhost:9090/api/v1/query?query=up' | jq`

## See Also

- [SKILL.md](../SKILL.md) - Main troubleshooting workflow
- [Docker Commands Reference](docker-commands.md) - Container debugging
- [Common Issues & Solutions](common-issues.md) - Known problems
