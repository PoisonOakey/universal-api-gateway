# Future Roadmap & Hardening

Two tables. **Planned** is a tracker — delete a row once it ships. **Not Built Yet** records what the repository does not do, so nothing here implies otherwise.

---

## Planned

| Item | What it adds | Closes gap | Effort |
|---|---|---|---|
| **Tests for the five uncovered paths** | Covers retry/backoff, 504 and 502 error mapping, the `/readyz` 503 branch, `POST`/`PUT` body forwarding, and hop-by-hop response header stripping. Would let the coverage floor rise from 75% toward 90% | *Error and forwarding paths are untested* | 45 min |
| **`PodDisruptionBudget` + `podAntiAffinity`** | Stops all pods being evicted at once; spreads them across nodes | *No PDB or anti-affinity* | 20 min |
| **`HorizontalPodAutoscaler`** | Scales 2→10 replicas on CPU/memory. Only meaningful on a live cluster | — | 20 min |
| **Prometheus + Grafana stack** | The app exposes `/metrics` but nothing scrapes or displays it. Compose stack, pattern reusable from `ztp-linux-node/monitoring/` | — | 45 min |
| **SLOs + recording rules** | Availability and latency objectives as Prometheus recording rules. Alerts exist; objectives do not | — | 45 min |
| **Ingress + TLS** | Replaces `NodePort`/`LoadBalancer` with a hostname and a certificate | *No Ingress or TLS* | 30 min |

---

## Not Built Yet

Known gaps, recorded so the repository does not imply otherwise:

| Gap | What this means today |
|---|---|
| **No cluster is running** | The manifests have been applied to a real AKS cluster and served traffic on a public IP, then destroyed. Nothing is running now, and no cluster is kept alive between demonstrations. Rolling updates, node failure, and sustained load remain unobserved — a cluster that lives for thirty minutes is not evidence about any of them. |
| **No PodDisruptionBudget or anti-affinity** | Two replicas protect against a pod crash, not a node failure. On a single-node cluster both pods share a node. This is not high availability. |
| **Rate limiting is per-pod and in memory** | `slowapi` holds counters in process. At 2 replicas the effective limit is 200 req/min, not the configured 100. A shared store such as Redis would be needed to make the limit cluster-wide. |
| **Image tag is `latest` on the local path** | The root kustomization relies on `universal-api-gateway:latest` with `imagePullPolicy: IfNotPresent`. Only the cloud overlay pins a specific SHA tag. |
| **Cloud overlay requires pushed commits** | The cloud overlay uses a remote base pinned to a commit SHA. Local edits to configuration or manifests will not apply to the cluster until they are pushed to GitHub and the ref is bumped. CI validates the overlay at that pinned commit, not your working tree — the base build in the same job is what covers the working tree. |
| **No Ingress or TLS** | Exposure is a `NodePort` on 30000. Traffic is plain HTTP. |
| **No config hot-reload** | `config/gateway.yaml` is read once at startup. Changing routes requires a pod restart. |
| **Five code paths in `src/main.py` are untested** | Coverage is 80% and CI floors it at 75%, but the misses are not evenly spread — they are concentrated in the paths that only run when something goes wrong. Specifically: the `tenacity` retry and backoff behaviour, the `504`/`502` mapping for upstream timeouts and connection errors, the `/readyz` 503 branch when no routes load, `POST`/`PUT` body forwarding, and hop-by-hop response header stripping. The happy path, auth rejection, rate limiting, and the health and metrics endpoints *are* covered. |
| **`POST` proxying is unverified on the current dependency stack** | v0.8.0 moved `starlette` across a major version (0.37 → 1.4) to clear CVE-2024-47874. Body forwarding and response header filtering are the two places that touch Starlette's `Request`/`Response` internals, and both are among the untested paths above. The suite and a container smoke test passed, but that smoke test issued only `GET` requests. A `POST` through the gateway to a real upstream has not been exercised since the upgrade. |
| **Terminating pods are not drained** | There is no `preStop` hook or tuned `terminationGracePeriodSeconds`, so Kubernetes may route to a pod that is shutting down. |
