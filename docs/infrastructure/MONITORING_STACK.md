# Monitoring Stack Configuration

## Overview

RawDrive uses a comprehensive observability stack:

| Component | Port | Purpose |
|-----------|------|---------|
| Prometheus | 9090 | Metrics collection & alerting |
| Grafana | 3001 | Dashboards & visualization |
| Loki | 3100 | Log aggregation |
| Promtail | - | Log shipping |
| Alertmanager | 9093 | Alert routing |

## Access URLs

### Docker Compose
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- Loki: http://localhost:3100

### Kubernetes
```bash
# Port forward Grafana
kubectl port-forward svc/grafana 3001:3000 -n RawDrive

# Port forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n RawDrive
```

## Prometheus Configuration

### Scrape Targets

| Target | Endpoint | Interval |
|--------|----------|----------|
| Traefik | :8082/metrics | 15s |
| PostgreSQL | :9187/metrics | 30s |
| Redis | :9121/metrics | 30s |
| Kafka | :9308/metrics | 30s |
| Backend | :8000/metrics | 15s |
| Gallery Service | :8004/metrics | 15s |
| All Microservices | :800x/metrics | 15s |

### Key Metrics

**Traefik (API Gateway)**:
- `traefik_service_requests_total` - Request count by service
- `traefik_service_request_duration_seconds` - Latency histogram
- `traefik_entrypoint_requests_total` - Requests by entry point

**Application**:
- `http_requests_total` - HTTP request count
- `http_request_duration_seconds` - Request latency
- `active_connections` - Current connections

**Database**:
- `pg_stat_activity_count` - Active connections
- `pg_database_size_bytes` - Database size
- `pg_replication_lag` - Replication lag

**Redis**:
- `redis_memory_used_bytes` - Memory usage
- `redis_connected_clients` - Client count
- `redis_commands_processed_total` - Command count

**Kafka**:
- `kafka_consumergroup_lag` - Consumer lag
- `kafka_topic_partition_current_offset` - Current offset

## Alert Rules

### Critical Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| ServiceDown | `up == 0` for 1m | critical |
| HighErrorRate | Error rate > 5% for 5m | critical |
| KafkaPartitionOffline | Leader = -1 | critical |
| RedisRejectingConnections | Rejections > 0 | critical |

### Warning Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighLatency | P95 > 500ms for 5m | warning |
| PostgresConnectionsHigh | > 80% max for 5m | warning |
| RedisMemoryHigh | > 90% max for 5m | warning |
| KafkaConsumerLagHigh | Lag > 1000 for 10m | warning |
| DiskSpaceLow | > 85% used | warning |

## Grafana Dashboards

### Services Overview Dashboard

Panels:
1. **Services Up** - Count of healthy services
2. **Total Request Rate** - Aggregate RPS
3. **Error Rate** - 5xx percentage
4. **P95 Latency** - Overall latency
5. **Request Rate by Service** - Per-service RPS
6. **Latency by Service** - Per-service P95
7. **PostgreSQL Connections** - Active connections
8. **Redis Memory** - Used vs max
9. **Kafka Consumer Lag** - Per consumer group

### Creating Custom Dashboards

1. Open Grafana: http://localhost:3001
2. Click "+" → "New Dashboard"
3. Add panels with Prometheus queries

Example query for request rate:
```promql
sum(rate(traefik_service_requests_total[1m])) by (service)
```

## Loki Log Aggregation

### Log Labels

Logs are labeled by:
- `service` - Service name
- `container` - Container name
- `level` - Log level (info, warn, error)
- `trace_id` - Distributed trace ID

### Querying Logs

In Grafana → Explore → Loki:

```logql
# All errors from backend
{service="backend"} |= "error"

# Errors in last hour
{service=~".*"} | json | level="error"

# Specific request trace
{service=~".*"} |= "trace_id=abc123"
```

### Log Retention

- **Default**: 31 days
- **Configurable** in `loki-config.yaml`:
```yaml
limits_config:
  retention_period: 744h  # 31 days
```

## Promtail Configuration

### Docker Log Collection

```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
```

### Log Parsing

JSON logs from FastAPI services:
```yaml
pipeline_stages:
  - json:
      expressions:
        level: level
        message: message
        trace_id: trace_id
  - labels:
      level:
      trace_id:
```

## Alert Routing (Alertmanager)

### Configuration

```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack'
```

### Receivers

Configure in Alertmanager:
- **Slack**: Webhook URL
- **PagerDuty**: Integration key
- **Email**: SMTP settings

## Useful PromQL Queries

### Request Rate
```promql
sum(rate(traefik_service_requests_total[5m])) by (service)
```

### Error Rate
```promql
sum(rate(traefik_service_requests_total{code=~"5.."}[5m]))
/ sum(rate(traefik_service_requests_total[5m]))
```

### P95 Latency
```promql
histogram_quantile(0.95,
  sum(rate(traefik_service_request_duration_seconds_bucket[5m])) by (le, service)
)
```

### Kafka Consumer Lag
```promql
sum(kafka_consumergroup_lag) by (consumergroup, topic)
```

### Redis Memory Usage
```promql
redis_memory_used_bytes / redis_memory_max_bytes * 100
```

## Troubleshooting

### Prometheus not scraping

1. Check target status: http://localhost:9090/targets
2. Verify service has `/metrics` endpoint
3. Check network connectivity

### Grafana dashboard empty

1. Verify data source connection
2. Test query in Explore
3. Check time range

### Logs not appearing in Loki

1. Check Promtail logs
2. Verify Docker socket access
3. Check label configuration
