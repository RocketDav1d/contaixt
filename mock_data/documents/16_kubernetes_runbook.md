---
doc_id: doc_016
title: "Kubernetes Operations Runbook"
author: Markus Lang
source_type: notion
---

# Kubernetes Operations Runbook

**Author:** Markus Lang (DevOps Lead)
**Contributors:** Sandra Hoffmann (CTO), Felix Braun (Senior Developer)
**Last Updated:** October 2025
**Applies to:** All TechVision AKS clusters

## Introduction

This runbook covers the operational procedures for managing our Azure Kubernetes Service (AKS) clusters. It provides guidance on cluster setup, namespace strategy, Helm chart standards, resource management, troubleshooting, certificate management, and upgrade procedures. This is a companion document to the Azure Cloud Architecture Reference Guide (doc_011) and the Monitoring & Alerting Runbook (doc_014).

All TechVision production workloads run on AKS. Our current clusters support Projekt Aurora, the FinSecure Portal, and MedTech Analytics, along with shared internal services (monitoring stack, ingress controllers, cert-manager).

---

## Cluster Setup

### AKS Configuration

All AKS clusters are provisioned via Terraform (see doc_011 for naming conventions and infrastructure-as-code requirements). The standard cluster configuration:

| Setting | Value |
|---|---|
| Kubernetes version | 1.28.x (latest stable minus one) |
| Network plugin | Azure CNI |
| Network policy | Calico |
| DNS service | CoreDNS |
| Ingress controller | NGINX Ingress Controller (Helm chart) |
| Certificate management | cert-manager (Helm chart) |
| Monitoring | Prometheus Operator (kube-prometheus-stack Helm chart) |
| Secret management | Azure Key Vault CSI Driver |
| Identity | Workload Identity (Azure AD) |

### Node Pools

Each cluster has three node pools with distinct responsibilities:

**System Pool:**
- **Purpose:** Kubernetes system components (CoreDNS, kube-proxy, monitoring agents).
- **VM Size:** Standard_D4s_v5 (4 vCPU, 16 GB RAM).
- **Node Count:** 3 (fixed, no autoscaling).
- **Taints:** `CriticalAddonsOnly=true:NoSchedule` — only system pods with the corresponding toleration are scheduled here.
- **OS Disk:** 128 GB Premium SSD.

**Workload Pool:**
- **Purpose:** Application workloads (APIs, web servers, background workers).
- **VM Size:** Standard_D8s_v5 (8 vCPU, 32 GB RAM).
- **Node Count:** 3-12 (Cluster Autoscaler enabled).
- **Taints:** None (default scheduling target).
- **Autoscale triggers:** Scale up when any pod is pending for > 30 seconds. Scale down when node utilization drops below 40% for 10 minutes.

**Data Pool:**
- **Purpose:** Memory-intensive workloads (database proxies, caching layers, data processing jobs).
- **VM Size:** Standard_E8s_v5 (8 vCPU, 64 GB RAM).
- **Node Count:** 2-6 (Cluster Autoscaler enabled).
- **Node Selector:** `workload-type: data` — pods requiring this pool specify a `nodeSelector`.
- **Used by:** PgBouncer, Redis, Projekt Aurora's data processing workers.

### Node Pool Maintenance

- Node images are auto-upgraded on a weekly schedule (Sunday 02:00-06:00 CET maintenance window).
- Node OS patching uses the `NodeImage` upgrade channel (latest security patches without Kubernetes version change).
- Cordon and drain operations are automated by AKS during upgrades. Applications must handle graceful shutdown (see resource limits section).

---

## Namespace Strategy

### Per-Team + Per-Environment Namespaces

```
{project}-{environment}
```

| Namespace | Project | Environment |
|---|---|---|
| `aurora-dev` | Projekt Aurora | Development |
| `aurora-staging` | Projekt Aurora | Staging |
| `aurora-prod` | Projekt Aurora | Production |
| `finsecure-dev` | FinSecure Portal | Development |
| `finsecure-staging` | FinSecure Portal | Staging |
| `finsecure-prod` | FinSecure Portal | Production |
| `medtech-dev` | MedTech Analytics | Development |
| `medtech-prod` | MedTech Analytics | Production |
| `monitoring` | Shared | Prometheus, Grafana, Loki |
| `ingress` | Shared | NGINX Ingress Controller |
| `cert-manager` | Shared | cert-manager |

### Namespace Configuration

Each namespace has:
- **ResourceQuota:** CPU and memory limits to prevent a single namespace from consuming the entire cluster.
- **LimitRange:** Default CPU/memory requests and limits applied to pods that do not specify them.
- **NetworkPolicy:** Default deny-all ingress. Explicit allow rules for required traffic (see network policies section below).

Example ResourceQuota (production namespace):
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: aurora-prod
spec:
  hard:
    requests.cpu: "32"
    requests.memory: "64Gi"
    limits.cpu: "64"
    limits.memory: "128Gi"
    pods: "100"
```

### Network Policies

Default deny-all policy in every namespace:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

Explicit allow policies added per service:
- Ingress from NGINX Ingress Controller namespace to application pods.
- Egress to database subnets (Azure SQL private endpoints, PgBouncer).
- Egress to monitoring namespace (Prometheus scrape).
- Egress to the internet via Azure Firewall for approved external APIs.

---

## Helm Chart Standards

### Chart Structure

All TechVision services are deployed via Helm charts stored in the application repository under `helm/{service-name}/`:

```
helm/aurora-api/
  Chart.yaml
  values.yaml
  values-dev.yaml
  values-staging.yaml
  values-prod.yaml
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    hpa.yaml
    configmap.yaml
    serviceaccount.yaml
    networkpolicy.yaml
    _helpers.tpl
```

### Values.yaml Structure

```yaml
# values.yaml — default values (dev-like)
replicaCount: 2
image:
  repository: tvsharedweucr.azurecr.io/aurora-api
  tag: "latest"  # Overridden by CI/CD
  pullPolicy: IfNotPresent
resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi
autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
ingress:
  enabled: true
  host: aurora-api.dev.techvision.de
  tls: true
env:
  LOG_LEVEL: debug
  DATABASE_POOL_SIZE: "5"
```

Environment-specific overrides in `values-prod.yaml`:
```yaml
replicaCount: 3
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 12
  targetCPUUtilizationPercentage: 70
ingress:
  host: aurora-api.prod.techvision.de
env:
  LOG_LEVEL: warning
  DATABASE_POOL_SIZE: "20"
```

### Chart Versioning

- Helm chart version (`Chart.yaml` `version` field) is independent of the application version (`appVersion`).
- Chart version follows semantic versioning.
- Application version matches the Docker image tag.
- The CI/CD pipeline (doc_013) sets `image.tag` during deployment via `--set image.tag={git-sha}`.

---

## Resource Limits

### Mandatory Resource Specifications

Every container must specify CPU and memory requests and limits. Pods without resource specifications will be rejected by the LimitRange admission controller.

**Guidelines:**
- **Requests** = expected normal usage. This is what the scheduler uses for placement.
- **Limits** = maximum allowed. Exceeding memory limits causes OOMKill. Exceeding CPU limits causes throttling.
- Set requests to approximately 70-80% of limits to allow for burst capacity.

### Horizontal Pod Autoscaler (HPA)

HPA is enabled for all production workloads:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aurora-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aurora-api
  minReplicas: 3
  maxReplicas: 12
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
```

Scale-down is intentionally slower than scale-up to avoid flapping.

### Graceful Shutdown

All services must handle `SIGTERM` gracefully:
- Stop accepting new requests.
- Finish in-progress requests/jobs.
- Close database connections.
- Exit within the `terminationGracePeriodSeconds` (default: 30 seconds, 300 seconds for workers).

---

## Troubleshooting Guide

### CrashLoopBackOff

**Symptom:** Pod repeatedly starts and crashes, with increasing restart delays.

**Investigation steps:**
1. Check pod logs: `kubectl logs {pod-name} -n {namespace} --previous` (the `--previous` flag shows logs from the last crash).
2. Check pod events: `kubectl describe pod {pod-name} -n {namespace}` — look at the Events section.
3. Common causes:
   - Application error on startup (missing config, failed DB connection). Check environment variables and secrets.
   - Liveness probe failing too aggressively. Increase `initialDelaySeconds` and `failureThreshold`.
   - OOMKill on startup (memory limit too low for initialization). Increase memory limit.
4. If the application depends on an external service (database, message broker), verify the dependency is reachable: `kubectl exec -it {pod-name} -n {namespace} -- curl {service-url}`.

### OOMKilled

**Symptom:** Pod terminated with reason `OOMKilled`. Exit code 137.

**Investigation steps:**
1. Check current memory limit: `kubectl describe pod {pod-name} -n {namespace}` — find `resources.limits.memory`.
2. Check Grafana for the pod's memory usage trend. Is it a gradual leak or a sudden spike?
3. Gradual increase = memory leak. Profile the application (Python: `tracemalloc`, Java: heap dump with `jmap`).
4. Sudden spike = specific operation consuming too much memory (loading large files, unbounded query results).
5. Immediate fix: Increase the memory limit in the Helm values. Long-term: fix the memory issue in the application.
6. For the Projekt Aurora data pipeline: Large batch sizes in data processing jobs are a common cause. Reduce `BATCH_SIZE` environment variable.

### ImagePullBackOff

**Symptom:** Pod stuck in `ImagePullBackOff` state.

**Investigation steps:**
1. Check pod events: `kubectl describe pod {pod-name} -n {namespace}` — look for image pull error details.
2. Common causes:
   - **Image does not exist:** Verify the image tag in the Helm values matches an image in Azure Container Registry. Check CI/CD pipeline for build failures (doc_013).
   - **Authentication failure:** Verify the AKS cluster has the `AcrPull` role on the container registry. Check: `az aks check-acr --resource-group {rg} --name {aks-name} --acr tvsharedweucr.azurecr.io`.
   - **Rate limiting:** If pulling from Docker Hub (for third-party images), we may be rate-limited. Use the ACR mirror for public images.
3. Try pulling the image manually: `az acr repository show-tags --name tvsharedweucr --repository {image-name}`.

### Pending Pods

**Symptom:** Pod stuck in `Pending` state.

**Investigation steps:**
1. Check pod events: `kubectl describe pod {pod-name} -n {namespace}`.
2. Common causes:
   - **Insufficient resources:** Cluster Autoscaler cannot provision new nodes (quota limits, VM size unavailable). Check `kubectl get events -n kube-system | grep autoscaler`.
   - **Node affinity/selector mismatch:** Pod requests a node pool that does not exist or has no available capacity.
   - **PersistentVolumeClaim pending:** Volume provisioning failed. Check PVC status: `kubectl get pvc -n {namespace}`.
   - **ResourceQuota exceeded:** Namespace quota reached. Check: `kubectl describe resourcequota -n {namespace}`.

---

## Certificate Management

### cert-manager + Let's Encrypt

All TLS certificates are managed automatically by cert-manager:

- **Issuer:** Let's Encrypt (production for prod, staging for dev/staging environments).
- **Challenge type:** DNS-01 via Azure DNS (supports wildcard certificates).
- **Renewal:** cert-manager automatically renews certificates 30 days before expiry.

**ClusterIssuer configuration:**
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v2.api.letsencrypt.org/directory
    email: devops@techvision.de
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - dns01:
          azureDNS:
            subscriptionID: {subscription-id}
            resourceGroupName: tv-shared-weu-rg-dns
            hostedZoneName: techvision.de
            managedIdentity:
              clientID: {managed-identity-client-id}
```

### Certificate Monitoring

- cert-manager exposes Prometheus metrics for certificate status and expiry.
- Alert configured: P3 at 14 days before expiry, P1 at 24 hours (see doc_014).
- Dashboard: `grafana.internal.techvision.de/d/cert-manager`.

---

## Upgrade Procedure

### Pre-Upgrade Checklist

1. Review AKS release notes for the target Kubernetes version.
2. Check deprecated API versions: Run `kubent` (kube-no-trouble) to identify manifests using deprecated APIs.
3. Test the upgrade in a dev cluster first. Run integration tests against the upgraded cluster.
4. Notify stakeholders via `#infrastructure` Slack channel. Schedule the maintenance window.
5. Ensure monitoring is healthy and baselines are established (doc_014).

### Upgrade Steps

**1. Control Plane Upgrade:**

```bash
# Check available versions
az aks get-upgrades --resource-group tv-prd-weu-rg-aurora --name tv-prd-weu-aks-aurora

# Upgrade control plane only (no node pools)
az aks upgrade \
  --resource-group tv-prd-weu-rg-aurora \
  --name tv-prd-weu-aks-aurora \
  --kubernetes-version 1.29.0 \
  --control-plane-only
```

The control plane upgrade is non-disruptive. API server may be briefly unavailable (< 1 minute).

**2. Node Pool Upgrades (one at a time):**

```bash
# Upgrade system pool first
az aks nodepool upgrade \
  --resource-group tv-prd-weu-rg-aurora \
  --cluster-name tv-prd-weu-aks-aurora \
  --name system \
  --kubernetes-version 1.29.0

# Then workload pool
az aks nodepool upgrade \
  --resource-group tv-prd-weu-rg-aurora \
  --cluster-name tv-prd-weu-aks-aurora \
  --name workload \
  --kubernetes-version 1.29.0

# Then data pool
az aks nodepool upgrade \
  --resource-group tv-prd-weu-rg-aurora \
  --cluster-name tv-prd-weu-aks-aurora \
  --name data \
  --kubernetes-version 1.29.0
```

Node pool upgrades use a surge strategy (one extra node provisioned, old nodes drained one at a time). This maintains capacity during the upgrade.

**3. Post-Upgrade Verification:**

1. Verify all nodes are `Ready`: `kubectl get nodes`.
2. Verify all pods are `Running`: `kubectl get pods --all-namespaces | grep -v Running`.
3. Check Grafana dashboards for anomalies in error rate, latency, and resource usage.
4. Run smoke tests against all production APIs.
5. Verify monitoring stack is collecting metrics and logs normally.

### Maintenance Window

- **Production upgrades:** Saturday 02:00-06:00 CET. Markus Lang and one additional DevOps engineer must be present.
- **Dev/Staging upgrades:** Any business day, during business hours.
- Emergency patches (critical CVEs) may be applied outside the window with CTO approval and on-call coverage.

### Rollback

AKS does not support in-place Kubernetes version downgrade. If the upgrade causes issues:

1. Scale up the old node pool version (if still available).
2. Cordon and drain upgraded nodes.
3. As a last resort, recreate the cluster from Terraform and redeploy applications. Our infrastructure-as-code approach (doc_011) ensures the cluster can be fully recreated within the RTO window.

---

## Access Control

- **Cluster admin:** Markus Lang, Sandra Hoffmann (break-glass only).
- **Namespace admin:** Project leads have admin access to their project namespaces.
- **Developer access:** Read-only access to dev/staging namespaces. No direct production access — all changes via CI/CD (doc_013).
- Authentication via Azure AD. RBAC roles assigned via Terraform-managed role bindings.

For access requests or questions, contact Markus Lang in `#devops` on Slack.
