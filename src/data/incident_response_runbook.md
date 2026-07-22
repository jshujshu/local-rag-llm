# Incident Response Runbook (IT Operations)

## Purpose
This document outlines the standard procedures for responding to production incidents in the cloud infrastructure environment.

## Severity Levels

SEV1 - Critical Outage
- Complete service unavailability
- Data loss or corruption
- Security breach in progress

SEV2 - Major Degradation
- Partial outage affecting multiple users
- High latency (>2s API response time)
- Elevated error rates (>5%)

SEV3 - Minor Issue
- Isolated user impact
- Non-critical feature failure
- Cosmetic or logging issues

---

## Initial Response Procedure

1. Acknowledge the alert
   - Respond within 5 minutes for SEV1/SEV2 incidents
   - Use PagerDuty or equivalent alerting system

2. Assess impact
   - Identify affected services
   - Check dashboards (Datadog, Grafana)
   - Determine scope (region, AZ, global)

3. Mitigate if possible
   - Roll back recent deployments
   - Disable feature flags via LaunchDarkly
   - Scale infrastructure horizontally if needed

4. Communicate
   - Post updates in #incident-response Slack channel
   - Notify stakeholders via Statuspage.io

---

## Escalation Path

L1 Support Engineer → Initial triage  
L2 SRE Team → Infrastructure and scaling issues  
L3 Engineering → Code-level fixes  
Security Team → Suspected breaches  

---

## Common Commands

Kubernetes Checks:
- kubectl get pods -A
- kubectl describe pod <pod-name>
- kubectl logs <pod-name> --tail=100

System Metrics:
- top
- htop
- df -h
- iostat -x 1

---

## Post-Incident Steps

1. Conduct root cause analysis (RCA)
2. Document timeline of events
3. Identify corrective actions
4. Schedule postmortem meeting within 48 hours
5. Add preventive monitoring or alerts

---

## Related Tools
- Prometheus (metrics)
- Grafana (dashboards)
- PagerDuty (alerting)
- Splunk (log aggregation)