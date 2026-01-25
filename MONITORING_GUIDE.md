# Monitoring & Alerting Guide

## Overview

This guide describes the monitoring and alerting setup for the TokenLab Vesting Simulator application.

## Health Check Endpoint

### Endpoint: `GET /api/v1/health`

Returns application health status with system metrics.

**Response Example:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "cpu_percent": 15.2,
  "memory_percent": 45.8
}
```

### Monitoring Setup

#### 1. Basic Health Monitoring

Use a monitoring service to periodically check the health endpoint:

```bash
# Example with curl
curl http://localhost:8000/api/v1/health

# Expected response: 200 OK with "status": "healthy"
```

**Recommended check frequency**: Every 30 seconds

#### 2. Uptime Monitoring

Services like UptimeRobot, Pingdom, or StatusCake can monitor the health endpoint:

- **URL**: `https://your-domain.com/api/v1/health`
- **Interval**: 30-60 seconds
- **Alert on**: HTTP status code != 200 or response time > 5s

#### 3. Application Logging

The application logs to:
- **Console**: stdout (captured by container orchestration)
- **File**: `backend/app.log`

**Log levels**:
- INFO: Normal operations (requests, responses, simulation runs)
- WARNING: Validation errors, configuration issues
- ERROR: Simulation failures, exceptions

**Log format**:
```
2026-01-25 11:45:23 - app.main - INFO - Request: POST /api/v1/simulate
2026-01-25 11:45:23 - app.api.routes.simulation - INFO - Starting simulation: mode=tier1, horizon=36 months
2026-01-25 11:45:24 - app.api.routes.simulation - INFO - Simulation completed successfully in 1234.56ms, warnings=1
2026-01-25 11:45:24 - app.main - INFO - Response: POST /api/v1/simulate Status=200 Time=1.245s
```

#### 4. System Metrics

The health endpoint provides:
- **uptime_seconds**: Application uptime (for restart detection)
- **cpu_percent**: CPU usage percentage
- **memory_percent**: Memory usage percentage

**Alert thresholds** (recommended):
- CPU > 80% for 5 minutes → Warning
- CPU > 95% for 2 minutes → Critical
- Memory > 85% for 5 minutes → Warning
- Memory > 95% for 2 minutes → Critical

## Production Monitoring Recommendations

### Essential Monitoring (Minimum)

1. **Health Check Monitoring**
   - Service: UptimeRobot (free tier), Pingdom, or StatusCake
   - Alert on downtime > 1 minute

2. **Log Aggregation**
   - Service: Papertrail, Loggly, or CloudWatch Logs
   - Collect logs from stdout/stderr
   - Alert on ERROR logs

3. **Basic Metrics**
   - Monitor health endpoint metrics (CPU, memory, uptime)
   - Alert on threshold breaches

### Advanced Monitoring (Recommended)

1. **Application Performance Monitoring (APM)**
   - Service: New Relic, Datadog, or Elastic APM
   - Track request latency, error rates, throughput
   - Monitor simulation execution times

2. **Infrastructure Monitoring**
   - Service: Prometheus + Grafana, Datadog, or CloudWatch
   - Monitor host CPU, memory, disk, network
   - Track container/pod health (if using Kubernetes)

3. **Log Analysis**
   - Service: ELK Stack, Splunk, or Datadog Logs
   - Parse structured logs
   - Create dashboards for:
     - Request volume by endpoint
     - Error rate trends
     - Simulation execution time percentiles (p50, p95, p99)

4. **Alerting Rules**
   ```
   # Error Rate
   - Alert: ERROR logs > 10 per minute
   - Severity: Warning

   # Response Time
   - Alert: p95 response time > 5 seconds
   - Severity: Warning

   # Availability
   - Alert: Health check fails for 2 consecutive checks
   - Severity: Critical

   # Resource Usage
   - Alert: CPU > 80% for 5 minutes
   - Severity: Warning

   - Alert: Memory > 85% for 5 minutes
   - Severity: Warning
   ```

### Monitoring Integrations

#### Docker/Docker Compose

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### Kubernetes

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: backend
    livenessProbe:
      httpGet:
        path: /api/v1/health
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /api/v1/health
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
```

#### Prometheus (Advanced)

If you want to expose Prometheus metrics, add:

```python
# backend/requirements.txt
prometheus-fastapi-instrumentator==7.0.0

# backend/app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

# After app creation
Instrumentator().instrument(app).expose(app)
```

Then configure Prometheus to scrape `/metrics`.

## Alerting Channels

Configure alerts to be sent to:
- **Email**: For all alerts
- **Slack/Discord**: For critical alerts
- **PagerDuty/OpsGenie**: For on-call rotation (production only)
- **SMS**: For critical production outages

## Dashboard Recommendations

Create dashboards to visualize:

1. **Traffic Dashboard**
   - Requests per minute (by endpoint)
   - Response time (p50, p95, p99)
   - Error rate percentage

2. **System Dashboard**
   - CPU usage over time
   - Memory usage over time
   - Application uptime
   - Health check status

3. **Application Dashboard**
   - Simulations per hour
   - Average simulation execution time by tier
   - Validation error rate
   - Warning counts

4. **Error Dashboard**
   - Error count by type
   - Recent error logs
   - Error rate trends

## Testing Alerts

Before going to production, test your alerts:

```bash
# Simulate high CPU (Linux)
yes > /dev/null &

# Simulate application down
docker stop backend-container

# Simulate slow responses (add delay in code temporarily)
import time
time.sleep(10)  # in route handler
```

## Rollback Procedure

If alerts indicate problems:

1. Check logs for errors:
   ```bash
   tail -100 backend/app.log
   ```

2. Check health endpoint:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. If needed, rollback to previous version:
   ```bash
   git checkout v1.0.0  # or previous stable tag
   docker-compose down && docker-compose up -d --build
   ```

4. Monitor health endpoint until stable

## Maintenance Windows

Schedule maintenance windows for:
- Dependency updates: Monthly
- Database migrations: As needed
- Infrastructure changes: As needed

During maintenance:
- Set up maintenance page
- Notify users via status page
- Disable alerting temporarily

## Status Page

Consider setting up a status page:
- Service: StatusPage.io, Statuspage, or self-hosted
- Show current status of:
  - API availability
  - Response times
  - Scheduled maintenance
  - Incident history

## Contact & Escalation

Document:
- On-call schedule
- Escalation procedures
- Incident response runbook
- Contact information for team members

## Resources

- [FastAPI Monitoring Best Practices](https://fastapi.tiangolo.com/deployment/manually/)
- [Twelve-Factor App: Logs](https://12factor.net/logs)
- [SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
