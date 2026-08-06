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
