# Future Roadmap & Hardening

The current architecture establishes a config-driven and observable API Gateway engine. This document outlines what comes next, shifting focus from the application's internal correctness to the surrounding infrastructure and lifecycle automation.

The following items would take this gateway from a baseline Kubernetes Deployment to an autoscaling, managed workload.

---

## 1. Automated Elasticity (HPA)
**Objective**: Dynamically scale the number of gateway pods based on live traffic and resource consumption.
- **Implementation**: Introduce a Kubernetes `HorizontalPodAutoscaler` (HPA) manifest.
- **Details**: Configure the HPA to scale replicas from a minimum of 2 up to a maximum of 10, triggering a scale-up whenever average CPU utilization exceeds 75% or memory approaches limits.

## 2. High Availability Guarantees (PDB)
**Objective**: Prevent accidental downtime during cluster maintenance or node upgrades.
- **Implementation**: Introduce a Kubernetes `PodDisruptionBudget` (PDB) manifest.
- **Details**: Enforce `minAvailable: 1` (or `maxUnavailable: 1`) to ensure that Kubernetes never evicts all gateway pods simultaneously during voluntary node drains.

## 3. Automated Dependency Management
**Objective**: Eliminate technical debt and keep upstream dependencies secure without manual intervention.
- **Implementation**: Add a `.github/dependabot.yml` configuration.
- **Details**: Schedule weekly checks for both the `pip` packages (FastAPI, httpx, slowapi) and the `Docker` base image (Python alpine). Ensure pull requests are automatically generated when patches are released.

## 4. CI/CD Vulnerability Scanning
**Objective**: Prevent deploying images containing known CVEs (Common Vulnerabilities and Exposures).
- **Implementation**: Integrate a scanning tool like `Trivy` into the `.github/workflows/ci.yml` pipeline.
- **Details**: Configure the pipeline to scan the final `universal-api-gateway:latest` Docker image immediately after it is built. Force the CI to fail if any `CRITICAL` or `HIGH` severity vulnerabilities are detected in the OS or Python packages.

---

## Not Built Yet

Known gaps, recorded so the repository does not imply otherwise:

| Gap | What this means today |
|---|---|
| **No PodDisruptionBudget or anti-affinity** | Two replicas protect against a pod crash, not a node failure. On a single-node cluster both pods share a node. This is not high availability. |
| **Rate limiting is per-pod and in memory** | `slowapi` holds counters in process. At 2 replicas the effective limit is 200 req/min, not the configured 100. A shared store such as Redis would be needed to make the limit cluster-wide. |
| **Image tag is `latest` with `imagePullPolicy: IfNotPresent`** | A rollout can silently keep the old image. Digest or SHA tags are needed before this can be upgraded reliably. |
| **CI never publishes the image** | The build step runs with `push: false`, so the tag the manifests reference is not produced by CI. Deployment currently depends on a locally built image. |
| **No Ingress or TLS** | Exposure is a `NodePort` on 30000. Traffic is plain HTTP. |
| **No config hot-reload** | `config/gateway.yaml` is read once at startup. Changing routes requires a pod restart. |
| **Terminating pods are not drained** | There is no `preStop` hook or tuned `terminationGracePeriodSeconds`, so Kubernetes may route to a pod that is shutting down. |
