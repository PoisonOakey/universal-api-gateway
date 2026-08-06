# Future Roadmap & Hardening

Two tables. **Planned** is a tracker — delete a row once it ships. **Not Built Yet** records what the repository does not do, so nothing here implies otherwise.

---

## Planned

| Item | What it adds | Closes gap | Effort |
|---|---|---|---|
| **Trivy scan in CI** | Scan the built image in `ci.yml`; fail on `CRITICAL`/`HIGH` CVEs | — | 15 min |
| **`PodDisruptionBudget` + `podAntiAffinity`** | Stops all pods being evicted at once; spreads them across nodes | *No PDB or anti-affinity* | 20 min |
| **`HorizontalPodAutoscaler`** | Scales 2→10 replicas on CPU/memory. Only meaningful on a live cluster | — | 20 min |
| **Dependabot** | `.github/dependabot.yml`, weekly checks on pip packages and the base image | — | 10 min |
| **Prometheus + Grafana stack** | The app exposes `/metrics` but nothing scrapes or displays it. Compose stack, pattern reusable from `ztp-linux-node/monitoring/` | — | 45 min |
| **SLOs + recording rules** | Availability and latency objectives as Prometheus recording rules. Alerts exist; objectives do not | — | 45 min |
| **Ingress + TLS** | Replaces `NodePort`/`LoadBalancer` with a hostname and a certificate | *No Ingress or TLS* | 30 min |
| **Apply `terraform/gke/`** | Written and validated, never run — blocked on GCP billing | *GKE Terraform never applied* | 30 min |

---

## Not Built Yet

Known gaps, recorded so the repository does not imply otherwise:

| Gap | What this means today |
|---|---|
| **No cluster is running** | The manifests have been applied to a real AKS cluster and served traffic on a public IP, then destroyed. Nothing is running now, and no cluster is kept alive between demonstrations. Rolling updates, node failure, and sustained load remain unobserved — a cluster that lives for thirty minutes is not evidence about any of them. |
| **The GKE Terraform has never been applied** | `terraform/gke/` passes `validate` and `fmt -check` but has never created anything: GCP billing was unavailable on this account. Only `terraform/aks/` has run. |
| **No PodDisruptionBudget or anti-affinity** | Two replicas protect against a pod crash, not a node failure. On a single-node cluster both pods share a node. This is not high availability. |
| **Rate limiting is per-pod and in memory** | `slowapi` holds counters in process. At 2 replicas the effective limit is 200 req/min, not the configured 100. A shared store such as Redis would be needed to make the limit cluster-wide. |
| **Image tag is `latest` on the local path** | The root kustomization relies on `universal-api-gateway:latest` with `imagePullPolicy: IfNotPresent`. Only the GKE overlay pins a specific SHA tag. |
| **GKE overlay requires pushed commits** | The GKE overlay uses a remote base. Local edits to configuration or manifests will not apply to the cluster until they are pushed to GitHub. |
| **No Ingress or TLS** | Exposure is a `NodePort` on 30000. Traffic is plain HTTP. |
| **No config hot-reload** | `config/gateway.yaml` is read once at startup. Changing routes requires a pod restart. |
| **Terminating pods are not drained** | There is no `preStop` hook or tuned `terminationGracePeriodSeconds`, so Kubernetes may route to a pod that is shutting down. |
