---
name: troubleshooting
description: Systematic debugging workflow for RawDrive issues. Use when troubleshooting bugs, performance problems, service failures, or unexpected behavior.
---

# Troubleshooting & Debugging

## When to Use This Skill

Use this skill when:
- Debugging bugs or errors in RawDrive services
- Investigating performance issues or high latency
- Troubleshooting service failures or crashes
- Analyzing unexpected behavior
- Responding to alerts from Alertmanager
- Post-mortem analysis of incidents

**CRITICAL:** This skill enforces CLAUDE.md's debugging protocol. You MUST investigate first before making changes.

## Key Files

| Purpose | Location |
|---------|----------|
| Docker stack | `infrastructure/docker/docker-compose.yml` |
| Prometheus config | `infrastructure/monitoring/prometheus/prometheus.yaml` |
| Alert rules | `infrastructure/monitoring/prometheus/alerts.yaml` |
| Grafana dashboards | `infrastructure/monitoring/grafana/dashboards/` |
| Loki config | `infrastructure/monitoring/loki/loki-config.yaml` |
| Promtail config | `infrastructure/monitoring/promtail/promtail-config.yaml` |
| Health checks | `services/*/src/app/observability/health.py` |
| Metrics | `services/*/src/app/observability/metrics.py` |
| Structured logging | `services/*/src/app/core/logging.py` |
| Error handlers | `services/*/src/app/middleware/error_handler.py` |

## 6-Phase Debugging Workflow

### Phase 1: Investigate First (MANDATORY)

**NEVER skip this phase. Read actual errors before making assumptions.**

```bash
# Check error logs, health status, and metrics
docker compose logs --tail=100 [service-name] | grep -E "(ERROR|CRITICAL)"
docker compose ps && curl http://localhost:[port]/health
open http://localhost:3001  # Grafana dashboard
curl 'http://localhost:9090/api/v1/query?query=up{job="[service]"}'
```

**Checklist:** Read error messages, check /health endpoints, review logs, verify Grafana metrics, check Prometheus alerts, use Explore agent for code paths.

### Phase 2: Enable Diagnostics

Enable DEBUG mode in docker-compose.yml or .env:
```yaml
environment:
  DEBUG: "true"
  LOG_LEVEL: "DEBUG"
  DB_ECHO: "true"  # Only for database issues
```

Rebuild: `docker compose up -d --build [service-name]`

Add temporary logs with correlation IDs:
```python
logger.debug("Processing", request_id=request_id, user_id=user_id)
```

**Never:** Leave DEBUG enabled indefinitely, enable DB_ECHO in production, use print() statements.

### Phase 3: Capture Evidence

Reproduce while tailing logs: `docker compose logs -f [service-name]`

Extract correlation IDs from JSON logs: `request_id`, `trace_id`, `user_id`, `workspace_id`

Query Loki by correlation ID:
```bash
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="[service]"} |= "[request_id]"' | jq
```

Capture metrics snapshot:
```bash
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' | jq
```

Export Grafana dashboard: Share → Export → Save. See [observability-tools.md](references/observability-tools.md) for complete query examples.

### Phase 4: Isolate Root Cause

Apply **5 Whys Method**: Why did login fail? → 500 error → DB timeout → pool exhausted → connections leaked → missing cleanup in error path.

**Correlate evidence:** Match logs (error messages), metrics (CPU/memory spikes), code (error location). Example: "DB timeout" log + pg_stat_activity_count=100 + missing async session cleanup in user.py:45.

**Narrow scope:** Test in isolation, disable features, check recent git changes, profile with py-spy if performance issue.

See [common-issues.md](references/common-issues.md) for known patterns.

### Phase 5: Implement and Verify Fix

Write fix with comment explaining root cause and incident reference. Add regression test to prevent recurrence.

```python
# Root cause: Connection leak in error path (incident abc123, 2026-01-14)
async def get_user(user_id: str) -> User:
    async with get_db_session() as db:  # Context manager ensures cleanup
        return (await db.execute(select(User).where(User.id == user_id))).scalar_one()
```

Deploy: `docker compose up -d --build [service-name]`

Verify for 1-2 hours: Monitor error rate, P95 latency, connection pool in Grafana. Run regression test.

### Phase 6: Cleanup and Document

Revert debug configs: Set `DEBUG=false`, `LOG_LEVEL=INFO`. Rebuild service.

Remove temporary logs. Document root cause with incident report including: severity, duration, correlation IDs, metrics, fix reference, prevention measures.

Update runbooks if new pattern discovered. See [common-issues.md](references/common-issues.md) for updating known issues.

## Quick Reference

### Common Scenarios

| Scenario | First Steps |
|----------|-------------|
| **Service won't start** | `docker compose ps` → check logs → verify health dependencies (postgres, redis) |
| **500 errors** | Check error logs → Grafana error rate → database/redis connectivity |
| **Slow requests** | Grafana P95 latency → check database query times → profile code |
| **High CPU** | `docker stats` → check metrics → profile with py-spy |
| **High memory** | `docker stats` → check for memory leaks → review object lifecycle |
| **Rate limit errors** | Check Redis metrics → review rate_limit_hit_total counter |
| **OAuth failures** | Query audit logs for oauth events → check provider credentials |
| **Database errors** | Check postgres logs → connection pool metrics → query slow log |

### Service Ports

| Service | Health | Metrics | Dashboard |
|---------|--------|---------|-----------|
| Backend | 8000/health | 8000/metrics | - |
| Onboarding | 8006/health | 8006/metrics | - |
| Gallery | 8004/health | 8004/metrics | - |
| Billing | 8005/health | 8005/metrics | - |
| Upload | 8008/health | 8008/metrics | - |
| Prometheus | - | - | :9090 |
| Grafana | - | - | :3001 |
| Alertmanager | - | - | :9094 |
| Traefik | - | :8082/metrics | :8080 |

### Log Levels

| Level | Purpose | When to Use |
|-------|---------|-------------|
| DEBUG | Detailed info | Temporary debugging only |
| INFO | Normal operations | Default for production |
| WARNING | Recoverable issues | Unexpected but handled |
| ERROR | Failed operations | Requires attention |
| CRITICAL | System failure | Immediate action required |

## Best Practices

### Do
- **Always investigate first** - Read actual errors before assuming
- **Use correlation IDs** - Track requests across services
- **Enable DEBUG temporarily** - Only while actively debugging
- **Capture evidence** - Logs, metrics, traces before making changes
- **Verify fixes** - Monitor metrics for 1-2 hours post-deploy
- **Document root cause** - Explain WHY, not just WHAT
- **Clean up** - Revert debug configs, remove temporary logs
- **Add regression tests** - Prevent issue from recurring

### Don't
- **Jump to conclusions** - Without reading logs/code
- **Enable DEBUG indefinitely** - Increases log volume, performance impact
- **Enable DB_ECHO in production** - Massive log spam
- **Use print()** - Use structured logging instead
- **Ignore correlation IDs** - Makes tracking impossible
- **Skip verification** - Fix might break other paths
- **Leave debug code** - Remove temporary instrumentation
- **Silence exceptions** - Always log errors with context

## Multi-Tenancy Debugging

**Always include workspace_id in queries:**

```bash
# Find logs for specific workspace
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="[service]"} |= "workspace_id" |= "[ws_id]"' | jq

# Check metrics per workspace (if labeled)
curl 'http://localhost:9090/api/v1/query?query=http_requests_total{workspace_id="[ws_id]"}' | jq
```

When debugging multi-tenant issues:
1. Verify workspace isolation - check database queries include workspace_id
2. Check workspace-specific resources (storage quotas, rate limits)
3. Verify tenant data segregation in Redis keys
4. Check workspace_id propagation through service calls

## See Also

- [Docker Commands Reference](references/docker-commands.md)
- [Observability Tools Guide](references/observability-tools.md)
- [Common Issues & Solutions](references/common-issues.md)
- CLAUDE.md - Debugging Protocol (mandatory reading)
