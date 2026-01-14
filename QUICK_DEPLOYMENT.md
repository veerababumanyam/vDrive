# vDrive Quick Deployment Reference

**For Impatient Developers** 🚀

---

## Deploy Everything (ALL 23 Services)

```bash
cd /Users/v13478/Desktop/vDrive
bash scripts/deploy-all-services.sh
```

**What it does**: Deploys ALL services without asking questions. No selective deployment.

---

## Check Status

```bash
cd infrastructure/docker
docker compose ps
```

---

## View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

---

## Stop Everything

```bash
cd infrastructure/docker
docker compose down
```

---

## Restart a Service

```bash
cd infrastructure/docker
docker compose restart backend
```

---

## Access Services

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Backend Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Website | http://localhost:8020 |
| Grafana | http://localhost:3001 (admin/admin) |
| Prometheus | http://localhost:9090 |
| Kafka UI | http://localhost:8081 |
| Traefik | http://localhost:8080 |

---

## Common Issues

**Port in use**:
```bash
lsof -i :5432  # Check what's using the port
docker compose stop postgres  # Stop the service
```

**Service won't start**:
```bash
docker compose logs -f [service-name]  # Check logs
docker compose restart [service-name]   # Restart
```

**Network error when building**:
- Wait 30-60 minutes for Docker registry to recover
- Retry: `bash scripts/deploy-all-services.sh`

---

## Full Documentation

- **Complete Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Current Status**: [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)
- **Project Structure**: [CLAUDE.md](CLAUDE.md)

---

**Philosophy**: Deploy ALL services by default. No exceptions. No selective deployment.
