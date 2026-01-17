# Docker Commands Reference

Quick reference for Docker debugging commands in RawDrive.

## Service Management

```bash
# Start
docker compose up -d [service-name]                    # Start service
docker compose up -d --build [service-name]            # Rebuild and start
docker compose up [service-name]                       # Foreground mode

# Stop
docker compose down                                    # Stop all
docker compose stop [service-name]                     # Stop one
docker compose kill [service-name]                     # Force stop

# Restart
docker compose restart [service-name]                  # Quick restart
docker compose up -d --build [service-name]            # Rebuild + restart

# Rebuild
docker compose build --no-cache [service-name]         # Clean rebuild
```

## Logs

```bash
# View
docker compose logs -f [service]                       # Tail logs
docker compose logs --tail=100 [service]               # Last 100 lines
docker compose logs --since 30m [service]              # Last 30 minutes
docker compose logs -f --timestamps [service]          # With timestamps

# Filter
docker compose logs [service] | grep ERROR             # Errors only
docker compose logs [service] | grep "request_id=abc"  # By request ID
docker compose logs [service] | grep -c ERROR          # Count errors
docker compose logs [service] | grep -oP 'request_id=\K[^"}\s]+'  # Extract IDs
```

## Service Status & Resources

```bash
# Status
docker compose ps                                      # All services
docker compose ps [service] | grep "(healthy)"         # Check health

# Health endpoints
curl http://localhost:8000/health                      # Backend
curl http://localhost:8006/health                      # Onboarding
curl http://localhost:8006/ready                       # Readiness

# Resources
docker stats                                           # Real-time usage
docker stats --no-stream                               # One-time snapshot
```

## Interactive Debugging

```bash
# Shell access
docker compose exec [service] bash                     # Open shell
docker compose exec [service] env                      # View env vars

# Database (PostgreSQL)
docker compose exec postgres psql -U RawDrive -d RawDrive  # Shell
docker compose exec postgres psql -U RawDrive -c '\dt'   # List tables
docker compose exec postgres psql -U RawDrive -d RawDrive -c 'SELECT count(*) FROM pg_stat_activity;'

# Redis
docker compose exec redis redis-cli                    # CLI
docker compose exec redis redis-cli KEYS '*'           # List keys
docker compose exec redis redis-cli INFO memory        # Memory usage

# Network
docker compose exec backend ping postgres              # Test connectivity
docker compose exec backend curl http://gallery-service:8004/health
```

## File Operations

```bash
# Copy
docker compose cp [service]:/path/in/container /local  # From container
docker compose cp /local [service]:/path/in/container  # To container

# View
docker compose exec [service] cat /path/to/file        # View file
docker compose exec [service] tail -f /path/to/file    # Tail file
docker compose exec [service] grep -r "term" /app/src/ # Search
```

## Common Issues

```bash
# Service won't start
docker compose ps -a [service]                         # Check exit status
docker compose logs --tail=50 [service]                # View crash logs
docker compose ps postgres redis                       # Check dependencies
lsof -i :8000                                          # Check port usage

# Container restarting
docker compose logs --tail=200 [service]               # View crash logs
docker update --restart=no RawDrive-[service]            # Stop auto-restart

# Network issues
docker compose exec [service] ping postgres            # Test connectivity
docker compose exec [service] cat /etc/hosts           # Check DNS

# Disk space
docker system df                                       # Check disk usage
docker volume prune                                    # Clean volumes (WARNING)
```

## Profiling & Cleanup

```bash
# Python profiling
docker compose exec backend pip install py-spy
docker compose exec backend py-spy top --pid 1          # Real-time
docker compose exec backend py-spy record -o profile.svg --pid 1 --duration 60

# Cleanup
docker compose rm [service]                            # Remove stopped
docker system prune                                    # Clean unused
docker system prune -a --volumes                       # Deep clean (WARNING)
```

## Service-Specific

```bash
# Backend (Python/FastAPI)
docker compose exec backend alembic upgrade head        # Run migrations
docker compose exec backend pytest                      # Run tests

# Frontend (React)
docker compose exec frontend npm install                # Install deps
docker compose exec frontend npm run build              # Build

# Kafka
docker compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092
docker compose exec kafka kafka-console-consumer.sh --topic [topic] --from-beginning --bootstrap-server localhost:9092
```

## Environment Variables

```bash
# View
docker compose exec [service] env                      # All vars
docker compose exec [service] echo $DEBUG              # Specific var

# Update
vim infrastructure/docker/.env                         # Edit .env
docker compose up -d --force-recreate [service]        # Apply changes
docker compose exec [service] env | grep DEBUG         # Verify
```

## See Also

- [SKILL.md](../SKILL.md) - Main troubleshooting workflow
- [Observability Tools Guide](observability-tools.md) - Prometheus, Grafana, Loki
- [Common Issues & Solutions](common-issues.md) - Known problems and fixes
