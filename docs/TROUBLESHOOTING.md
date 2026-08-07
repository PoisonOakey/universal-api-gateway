# Troubleshooting

Common issues and their fixes when working with this project.

---

## Docker

### Docker Desktop stuck at "Starting the Docker Engine"

**Symptoms:** Docker Desktop loads indefinitely and never reaches a ready state.

**Root Cause:** WSL2 backend is in a corrupted or hung state.

**Fix:**
```powershell
# Kill all Docker processes
Get-Process *docker* | Stop-Process -Force

# Reset the WSL backend
wsl --shutdown
wsl --update
```
Then reopen Docker Desktop and wait 30-60 seconds.

**Nuclear Option (if the above doesn't work):**
```powershell
wsl --shutdown
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
```
Reopen Docker Desktop — it will re-initialize from scratch.

---

### "Virtualization support not detected" after using VirtualBox

**Symptoms:** Docker Desktop refuses to start with the error: *"Docker Desktop failed to start because virtualisation support wasn't detected."*

**Root Cause:** VirtualBox (or scripts that configure it, such as ZTP provisioning tools) disables Hyper-V and the Virtual Machine Platform — both of which Docker Desktop requires to run its WSL2 backend. Running VirtualBox and Docker Desktop on the same Windows host creates a direct conflict.

**Fix:** Re-enable the required Windows features in an **elevated PowerShell (Admin)**:
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```
Then **reboot your machine**. Docker Desktop will work again after the restart.

> [!WARNING]
> Re-enabling these features will break VirtualBox. You cannot run both Docker Desktop (WSL2) and VirtualBox (Hyper-V disabled) on the same machine simultaneously. Switch between them as needed.

---

### `docker build` fails with "no matching manifest for windows/amd64"

**Root Cause:** Docker Desktop is set to Windows containers instead of Linux containers.

**Fix:** Right-click the Docker Desktop tray icon → **Switch to Linux containers**.

---

### Port already in use (`bind: address already in use`)

**Symptoms:** `docker run -p 30000:8000` fails because port 30000 is occupied.

**Fix:**
```powershell
# Find what is using port 30000
netstat -ano | findstr :30000

# Kill the process by PID
Stop-Process -Id <PID> -Force
```
Or simply map to a different host port: `docker run -p 30001:8000 universal-api-gateway`

---

## FastAPI / Uvicorn

### `ModuleNotFoundError: No module named 'api'`

**Root Cause:** Running uvicorn from the wrong directory, or the `COPY` path in the Dockerfile doesn't match the import structure.

**Fix (Local):**
```bash
# Run from the project root, not from inside src/
python -m uvicorn src.main:app --reload --port 8000
```

**Fix (Docker):** Ensure the Dockerfile copies source code to the correct working directory:
```dockerfile
WORKDIR /app
COPY src/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### CORS errors in the browser console

**Symptoms:** Frontend gets `Access-Control-Allow-Origin` errors when calling the API.

**Root Cause:** The API's CORS middleware is not allowing the frontend's origin.

**Current Config:**
The gateway reads from the `ALLOWED_ORIGINS` environment variable (defaults to `http://localhost,http://localhost:30000`).

**Fix:** Ensure your frontend's domain is explicitly added to the `ALLOWED_ORIGINS` environment variable. Note that `allow_credentials` is strictly disabled for security.

---

### 401 Unauthorized

**Symptoms:** The gateway returns an HTTP 401 Unauthorized when hitting a proxy route.

**Root Cause:** You did not provide the correct Bearer token in the `Authorization` header.

**Fix:** Ensure your request includes `Authorization: Bearer <your-token>`. The expected token is defined by the `API_AUTH_TOKEN` environment variable. If you don't want auth (local dev only), do not set `API_AUTH_TOKEN`.

---

### 502 Bad Gateway vs 504 Gateway Timeout

**Symptoms:** The gateway returns an HTTP 502 or 504 when proxying a request to an upstream service.

**Root Cause:**
- **504 Gateway Timeout:** The gateway took too long to connect to or read from the upstream service (currently hardcoded to a 30s read/write timeout).
- **502 Bad Gateway:** The upstream service actively refused the connection, failed to resolve DNS, or dropped the request unexpectedly.

**Fix:** Check the Gateway's structured logs in the console (you can grep for `level=ERROR` to filter out healthy traffic). Every request logs a `request_id`. Look for the error log matching that ID to see the exact `httpx` exception that caused the failure (this is kept hidden from the client response for security). Note that if the upstream failed with a 502/503/504 on a `GET` request, the gateway will automatically retry 3 times with exponential backoff before returning the final error to you.

---

### 429 Too Many Requests

**Symptoms:** The gateway returns an HTTP 429 Too Many Requests with headers like `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After`.

**Root Cause:** The client has sent more than 100 requests in a single minute to a specific proxy route. The built-in `slowapi` rate limiter blocked the request to prevent upstream abuse.

**Fix:** Wait for the `Retry-After` duration (or until the 1-minute window expires) before sending more requests. Note that the 100/min limit applies per route, so other routes will still be accessible.

**Multi-replica note:** the rate-limit counter is in-memory and per-pod. In the K8s Deployment (`replicas: 2`), a client's requests can land on either pod, so the *effective* ceiling is up to ~200/min rather than a hard 100/min — expect a request to occasionally get through when you thought the limit should have already been hit.

---

## Kubernetes (Local)

### Pods stuck in `ImagePullBackOff`

**Root Cause:** Kubernetes is trying to pull the image from a remote registry, but it only exists locally.

**Fix:** Set `imagePullPolicy: Never` in the deployment YAML:
```yaml
containers:
  - name: api
    image: universal-api-gateway:latest
    imagePullPolicy: Never
```
And make sure you built the image inside the same Docker context that Kubernetes uses (e.g., Docker Desktop's built-in cluster).

---

### `cycle detected` when rendering an overlay

**Symptoms:** `kubectl kustomize k8s/overlays/<name>` fails with *"cycle detected: candidate root '<repo>' contains visited root '<repo>/k8s/overlays/<name>'"*.

**Root Cause:** The overlay lives inside the directory tree of the base it references. Kustomize refuses this regardless of `--load-restrictor`, which only governs file loading, not root cycles.

**Fix:** Point the overlay at a remote base instead of a relative parent, pinned to a commit so the render is reproducible:
```yaml
resources:
  - github.com/<owner>/<repo>//?ref=<full-sha>
```
Moving the base into a sibling directory does not help here: the root `kustomization.yaml` generates a ConfigMap from `config/gateway.yaml`, which sits outside any `k8s/` subdirectory, so the kustomization root has to stay at the repository root.

> The trade-off is that the overlay renders what is on GitHub, not your working tree. Local edits do not apply until pushed.

---

### Cannot reach the service from `localhost`

**Root Cause:** Kubernetes services are only reachable inside the cluster by default.

**Fix:** Use `kubectl port-forward` to tunnel traffic (though it is now exposed via NodePort anyway):
```bash
kubectl port-forward svc/universal-api-gateway 30000:8000 -n gateway-system
```
Then access `http://localhost:30000/docs`.

---

## Cloud

Notes from actually deploying this. Both providers failed before either succeeded, and neither failure was visible from the Terraform.

### Azure: "The VM size of Standard_B2s is not allowed in your subscription"

**Symptoms:** `terraform apply` creates the resource group, then fails on the cluster with HTTP 400. The error lists "available" sizes that are all M-series, HB, FX or GPU — nothing small.

**Root Cause:** Trial subscriptions restrict the cheap general-purpose families. This is not a quota problem: `az vm list-usage` showed 4 vCPUs free in the `Standard BS` family while `Standard_B2s` itself was unavailable. It is also not regional — `Standard_B2s` was restricted in every region checked.

**Fix:** Find a size the subscription can actually create, then use it:
```powershell
az vm list-skus --location southeastasia --resource-type virtualMachines --all --output json |
  ConvertFrom-Json | Where-Object { $_.restrictions.Count -eq 0 } | Select-Object -ExpandProperty name
```
On a trial subscription this returned 197 of 1271 SKUs. `Standard_DC2s_v3` (2 vCPU) works and two of them exactly fill the 4 vCPU regional quota.

> `terraform validate` and `terraform plan` both pass against a config that cannot apply. Neither contacts the compute API to check SKU availability.

---

### Azure: confirm you cannot be charged before applying

A new subscription has a spending limit that **disables** the subscription when trial credit runs out, rather than charging the card. Verify it is on:
```bash
az rest --method get \
  --url "https://management.azure.com/subscriptions/<id>?api-version=2022-12-01" \
  --query "{quota:subscriptionPolicies.quotaId, limit:subscriptionPolicies.spendingLimit}"
```
`FreeTrial_*` with `spendingLimit: On` means charges are structurally impossible. Anything else means real money.

---

### GCP: `OR_BACR2_44` when setting up billing

**Symptoms:** *"Billing setup can't be completed. This action couldn't be completed. [OR_BACR2_44]"*

**Root Cause:** A provider-side block, usually a card Google declines or an account flagged from a previous trial. Nothing in the project or the Terraform causes it.

**Diagnosis:** Check whether a usable billing account exists at all:
```bash
gcloud auth application-default print-access-token   # then:
curl -s -H "Authorization: Bearer $TOKEN" https://cloudbilling.googleapis.com/v1/billingAccounts
```
`"open": false` means the account is closed and cannot be attached to any project. Creating a new project does not help — billing attaches to the billing account, not the project.

**Fix:** Google Cloud Billing Support resolves these; there is no self-service path. Otherwise use another provider.

---

### `az` or `terraform` "not recognized" straight after install

**Root Cause:** `winget` modifies `PATH` for new processes only.

**Fix:** Close the terminal and open a new one. If a script must not depend on `PATH`, call the binary directly — `C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd`.

---

### Confirming a cluster is really gone

`terraform destroy` only removes what it created. AKS also creates a node resource group it does not own, and a `LoadBalancer` Service creates a public IP owned by Kubernetes rather than Terraform. Check the subscription directly:
```bash
az group list --output table
az network public-ip list --output table
az aks list --output table
```
A lone `NetworkWatcherRG` is created automatically by Azure and carries no charge. Anything else is still billing.

---

## CI/CD (GitHub Actions)

Notes from hardening the pipeline. Two of the six gates failed the first time they were pointed at the repository, and neither failure was caused by anything the pipeline itself did wrong — both were pre-existing problems that nothing had been looking for.

### Trivy fails the build with dozens of CVEs the first time it runs

**Symptoms:** The `image` job fails immediately with a large table — in this repo, 48 fixable HIGH/CRITICAL (6 of them CRITICAL), nearly all in `debian` packages rather than in anything the project installs.

**Root Cause:** The Dockerfile pinned `python:3.12.4-slim`. A patch-level tag is immutable, so it freezes the entire OS layer at the day it was published — Debian 12.6, roughly two years stale. Every distro CVE disclosed since then accumulates in the image. Nothing in the project's own code or dependencies changed; the base simply rotted in place.

**Fix:** Move the pin up one level so the base tracks patch releases:
```dockerfile
FROM python:3.12-slim
```
This took the OS findings from 48 to 0 (Debian 13.6). The Python minor version is still pinned, so this is not an uncontrolled upgrade.

> [!TIP]
> The Dependabot `docker` ecosystem in `.github/dependabot.yml` exists specifically for this. It watches the base image and opens a PR when it moves, which is what stops the same drift from silently rebuilding over the next two years.

---

### Trivy reports a CVE in a package that is not in `requirements.txt`

**Symptoms:** After the base image is clean, three HIGH findings remain against `starlette` — a package the project never declares.

**Root Cause:** Trivy scans what is actually installed in the image, not what is declared. `starlette` is a transitive dependency of FastAPI, and `fastapi==0.111.0` constrains it to `>=0.37.2,<0.38.0`. The vulnerable version cannot be upgraded on its own; the pin holding it back is the direct dependency.

For a gateway, one of these is worth naming: **CVE-2024-47874** is a denial of service via `multipart/form-data`, reachable on any proxied `POST`.

**Fix:** Upgrade the *direct* dependency that pins the vulnerable transitive one:
```bash
pip install --upgrade fastapi
pip list --format=freeze | grep -iE '^(fastapi|starlette)=='
```
Then re-pin `requirements.txt` from the resolved output. Verify before committing — this crossed a starlette major version (0.37 → 1.4):
```bash
pytest                      # unit tests
docker build -t uag:test .  # then smoke-test the running container
```

---

### `pip-audit` fails on a test-only dependency

**Symptoms:** The `audit-deps` job fails on `PYSEC-2026-1845` in `pytest==8.2.2`, which never ships in the image.

**Root Cause:** The gate audits `requirements-dev.txt` as well as `requirements.txt`. This is deliberate: dev dependencies run with full access to the repository and to CI secrets, so a compromised test tool is a real supply-chain path even though it is not in the published artifact.

**Fix:** Bump the dev pin like any other. If a finding genuinely has no fix available yet, do not delete the step — narrow it, and leave a reason:
```bash
pip-audit -r requirements.txt -r requirements-dev.txt --ignore-vuln <ID>   # <reason + revisit date>
```

---

### The Trivy gate blocks on a CVE with no patch available

**Root Cause:** Distro packages routinely carry disclosed vulnerabilities with no fixed version released. Gating on those makes the pipeline unfixable — the only way to go green is to stop scanning.

**Fix:** The gate runs with `--ignore-unfixed`, so it only fails on findings that can actually be acted on. A second non-blocking step reports everything else, including unfixed and MEDIUM, so the full picture stays visible in the logs without holding up a release.

---

### Trivy cannot find the image the build just produced

**Symptoms:** The scan step errors with an image-not-found, even though the build step above it succeeded.

**Root Cause:** `docker/build-push-action` with `push: false` leaves the result in the buildx cache. It never enters the local Docker daemon, so nothing that talks to the daemon can see it.

**Fix:** Set `load: true` on the build step, which materialises the image into the daemon under its tag. This also matters for correctness: it is what lets the scan run against the exact image `publish` later pushes, rather than a separate rebuild.

---

### `terraform init` in CI wants credentials or remote state

**Root Cause:** A plain `init` configures the backend, which for most real configurations means reaching for state and cloud credentials. Neither should be needed just to check that the configuration is syntactically valid.

**Fix:** Initialise providers only:
```bash
terraform init -backend=false -input=false
terraform validate
```

> [!IMPORTANT]
> `terraform validate` checks syntax and types. It does **not** contact the compute API, so it passes against configurations that cannot actually apply — see *Azure: "The VM size of Standard_B2s is not allowed in your subscription"* above. Treat a green `validate-infra` job as "this will parse", not "this will deploy".

---

### `kustomize build` succeeds but the manifests are still wrong

**Root Cause:** Kustomize validates kustomize syntax. It does not check the rendered objects against the Kubernetes API — a misspelled field or a wrong `apiVersion` renders happily and fails at `kubectl apply`.

**Fix:** Pipe the render into a schema validator. The pipeline runs both, for the base and the cloud overlay:
```bash
kustomize build . > base.yaml
kubeconform -strict -summary -verbose < base.yaml
```

---

### The cloud overlay makes CI depend on GitHub being reachable

**Root Cause:** `k8s/overlays/cloud/kustomization.yaml` references a remote base pinned to a commit SHA (see *`cycle detected` when rendering an overlay* above). Building it performs a network fetch, so the `validate-infra` job depends on that repository staying public and that SHA staying reachable.

**Consequence to keep in mind:** the job validates the manifests *at that pinned commit*, not the ones in your working tree. A change to `k8s/api-deployment.yaml` on a branch is not covered by the overlay build until it is pushed and the ref is bumped. The base build in the same job does cover the working tree, which is why both run.

---

### `gitleaks` passes but never actually scanned the history

**Symptoms:** The secret scan reports success suspiciously fast and mentions only a commit or two.

**Root Cause:** `actions/checkout` does a shallow clone by default (`fetch-depth: 1`). Gitleaks then has almost no history to walk, so a secret committed and later removed — the exact case the gate exists to catch — is invisible. The job goes green while checking nothing.

**Fix:**
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```
A correct run states the number of commits scanned; this repo reports 43. If that number looks too small, the checkout is the problem.

---

### Ruff flags `Depends()` in a function signature (B008)

**Symptoms:** `ruff check` reports *function-call-in-default-argument* on every FastAPI dependency.

**Root Cause:** A false positive. B008 exists to catch mutable defaults evaluated once at definition time; `Depends()` is the framework's intended idiom and FastAPI resolves it per request.

**Fix:** Exempt it in `ruff.toml` rather than adding a `# noqa` to every route:
```toml
[lint.flake8-bugbear]
extend-immutable-calls = ["fastapi.Depends", "fastapi.Security"]
```

---

### `docker run -v` fails on Windows with a mangled path

**Symptoms:** Running the pipeline's container steps locally from Git Bash fails with something like *"the working directory 'D:/Git/app' is invalid, it needs to be an absolute path"* — note the injected `Git`.

**Root Cause:** MSYS (Git Bash) rewrites anything that looks like a POSIX path in an argument, so `/app` is expanded against the Git installation directory before Docker ever sees it.

**Fix:** Disable the rewriting for that command, and double up the leading slash on container-side paths:
```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "D:/universal-api-gateway:/src" -w //app <image>
```
PowerShell is not affected. This only bites when reproducing CI steps locally on Windows.
