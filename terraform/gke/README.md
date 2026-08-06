# GKE Cluster Terraform

Provisions a throwaway GKE cluster for testing the Universal API Gateway.

## What it creates
- A custom VPC and subnet.
- A **zonal** GKE cluster in `asia-southeast1-a` (Singapore).
- A separate node pool with 2 `e2-small` nodes.

## Cost Estimate
An `e2-small` node in `asia-southeast1` costs roughly ~$0.015/hour, plus 2 × 100GB default boot disks. The control plane management fee is ~$0.10/hour (note that the GKE free tier covers one zonal control plane per billing account). Total cost while running is approximately ~$0.13/hour (or ~$0.03/hour if the free tier applies).

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
