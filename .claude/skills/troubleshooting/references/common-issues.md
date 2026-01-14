# Common Issues & Solutions

Known issues in vDrive and their solutions, organized by category.

## Service Startup Issues

### Issue: Service Won't Start

**Symptoms:**
- Container exits immediately after starting
- `docker compose ps` shows "Exit 1" or similar

**Investigation:**
```bash
# Check exit reason
docker compose logs --tail=50 [service-name]

# Check dependencies
docker compose ps postgres redis
```

**Common Causes:**

1. **Database not ready**
   - Solution: Wait for postgres health check to pass
   ```bash
   docker compose ps postgres  # Wait for "(healthy)"
   ```

2. **Redis not ready**
   - Solution: Wait for redis health check
   ```bash
   docker compose ps redis  # Wait for "(healthy)"
   ```

3. **Missing environment variables**
   - Solution: Check required env vars exist
   ```bash
   docker compose config  # Shows merged config
   ```

4. **Port already in use**
   - Solution: Find and kill process using port
   ```bash
   lsof -i :8000  # Find process
   kill -9 [PID]  # Kill process
   ```

### Issue: Container Keeps Restarting

**Symptoms:**
- Service shows "Restarting (1) X seconds ago"
- High restart count

**Investigation:**
```bash
# View crash logs
docker compose logs --tail=100 [service-name]

# Check restart policy
docker inspect vDrive-[service-name] | jq '.[0].HostConfig.RestartPolicy'
```

**Common Causes:**

1. **Unhandled exception in startup code**
   - Solution: Fix exception, add error handling
   ```python
   # Bad
   DATABASE_URL = os.environ["DATABASE_URL"]  # KeyError if missing

   # Good
   DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/vDrive")
   if not DATABASE_URL:
       raise ValueError("DATABASE_URL environment variable required")
   ```

2. **Database migration failure**
   - Solution: Run migrations manually
   ```bash
   docker compose exec backend alembic upgrade head
   ```

## Database Issues

### Issue: Connection Pool Exhausted

**Symptoms:** "pool exhausted" errors, timeouts, `pg_stat_activity_count` at max

**Investigation:** Query `pg_stat_activity_count` metric

**Solutions:**
1. Fix connection leaks - use `async with get_db_session() as db:`
2. Increase pool_size temporarily (pool_size=20)
3. Kill idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle'`

### Issue: Slow Queries

**Symptoms:** High P95 latency, DB timeouts

**Investigation:** Enable DB_ECHO=true, check logs

**Solutions:**
1. Add missing indexes: `CREATE INDEX idx_users_email ON users(email)`
2. Fix N+1 queries - use `joinedload(Gallery.photos)`
3. Add workspace_id filter first for tenant isolation

### Issue: Database Deadlocks

**Symptoms:** "deadlock detected" errors

**Investigation:** Query `pg_stat_database_deadlocks` metric

**Solutions:**
1. Use consistent lock ordering - sort IDs before locking
2. Minimize transaction scope - don't hold locks during external API calls

## Redis Issues

### Issue: Out of Memory

**Symptoms:** "(OOM) command not allowed" errors

**Solutions:**
1. Increase maxmemory: `redis-server --maxmemory 1gb`
2. Find large keys: `redis-cli --bigkeys`
3. Set TTL: `await redis.setex(key, 3600, value)`

### Issue: Rate Limiting False Positives

**Symptoms:** Legitimate users blocked, high `rate_limit_hit_total`

**Solutions:**
1. Adjust thresholds in rate_limit.py
2. Whitelist internal IPs

## Authentication Issues

### Issue: JWT Token Expired

**Symptoms:** 401 errors, unexpected logouts

**Solutions:**
1. Increase ACCESS_TOKEN_EXPIRE_MINUTES
2. Implement refresh tokens
3. Check server time sync across containers

### Issue: OAuth Login Failures

**Symptoms:** "OAuth state mismatch", callback failures

**Solutions:**
1. Verify OAuth credentials in env vars
2. Ensure redirect URI matches provider settings exactly
3. Store state in Redis before redirect: `await redis.setex(f"oauth:state:{state}", 300, session_id)`

## Performance Issues

### Issue: High Latency

**Symptoms:** P95 > 500ms, timeouts

**Solutions:**
1. Fix slow queries (see Database section)
2. Add caching: `await redis.setex(f"workspace:{id}", 300, data)`
3. Use `run_in_executor` for blocking I/O

### Issue: High CPU

**Symptoms:** CPU 80-100%, slow responses

**Investigation:** Profile with `py-spy top`

**Solutions:**
1. Optimize algorithms (avoid O(n²))
2. Avoid regex on large strings - check with `in` first

## Kafka Issues

### Issue: Consumer Lag Growing

**Symptoms:** Messages not processed, high `kafka_consumer_group_lag`

**Solutions:**
1. Scale consumers - increase NUM_CONSUMERS
2. Batch processing: `await asyncio.gather(*[process_message(m) for m in messages])`
3. Restart stuck consumers: `docker compose restart [consumer-service]`

## File Upload Issues

### Issue: Upload Timeouts

**Symptoms:** Timeout errors on large files

**Solutions:**
1. Increase Traefik timeout in dynamic.yaml (writeTimeout: "5m")
2. Stream uploads: `async for chunk in file.stream(): await upload_chunk(chunk)`

## See Also

- [SKILL.md](../SKILL.md) - Main troubleshooting workflow
- [Docker Commands Reference](docker-commands.md) - Container debugging
- [Observability Tools Guide](observability-tools.md) - Prometheus, Grafana, Loki
