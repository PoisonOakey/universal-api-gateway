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

**Current Config (allows all origins for local dev):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> [!WARNING]
> `allow_origins=["*"]` is fine for local development but must be locked down to specific domains before any production deployment.

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

### Cannot reach the service from `localhost`

**Root Cause:** Kubernetes services are only reachable inside the cluster by default.

**Fix:** Use `kubectl port-forward` to tunnel traffic (though it is now exposed via NodePort anyway):
```bash
kubectl port-forward svc/universal-api-gateway 30000:8000 -n gateway-system
```
Then access `http://localhost:30000/docs`.
