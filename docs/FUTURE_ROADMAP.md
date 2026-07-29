# Future Roadmap & Hardening

While the current architecture establishes a robust, self-healing, and observable API Gateway engine, this document outlines the future roadmap for the project. The upcoming phases will shift the focus from the application's internal correctness to the surrounding production infrastructure and lifecycle automation.

The following items represent the planned roadmap for taking this gateway from a baseline Kubernetes Deployment to an autoscaling, fully-managed enterprise workload.

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
