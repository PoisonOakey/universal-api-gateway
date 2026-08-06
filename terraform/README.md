# GKE Cluster Terraform

Provisions a throwaway GKE cluster for testing the Universal API Gateway.

## What it creates
- A custom VPC and subnet.
- A **zonal** GKE cluster in `asia-southeast1-a` (Singapore).
- A separate node pool with 2 `e2-small` nodes.

## Cost Estimate
An `e2-small` node in `asia-southeast1` costs roughly ~$0.015/hour. The control plane management fee is ~$0.10/hour. Total cost while running is approximately ~$0.13/hour.

## How to use
1. Set your project ID:
   ```bash
   export TF_VAR_project_id="your-project-id"
   ```
2. Run `terraform init`.
3. Run `terraform apply`.

## How to destroy
Run the following command to destroy all resources and stop incurring costs:
```bash
terraform destroy
```
Make sure to check the GCP console to verify that the external LoadBalancer and its static IP have been completely removed.
