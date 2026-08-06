# AKS Cluster Terraform

Provisions a throwaway AKS cluster for running the Universal API Gateway on managed Kubernetes.

## What it creates

- A resource group, `gateway-rg`, holding everything below.
- An AKS cluster on the **Free** control plane tier, in `southeastasia` (Singapore).
- A node pool with 2 `Standard_B2s` nodes on 32GB OS disks.
- A system-assigned managed identity, so no service principal secret is created or stored in state.

## Cost estimate

The AKS control plane is free on the `Free` SKU. The nodes are not: two `Standard_B2s` cost roughly ~$0.09/hour combined, plus a small amount for the OS disks and, once a `LoadBalancer` Service exists, a public IP.

Call it **~$0.10/hour while running**, and nothing once destroyed.

A new Azure subscription starts with a spending limit enabled, which disables the subscription when the trial credit is exhausted rather than charging the card. Check yours before applying:

```bash
az rest --method get --url "https://management.azure.com/subscriptions/<subscription-id>?api-version=2022-12-01" --query "subscriptionPolicies.spendingLimit"
```

## How to use

1. Log in and set the subscription:
   ```bash
   az login
   export TF_VAR_subscription_id="<your-subscription-id>"
   ```
2. Run `terraform init`.
3. Run `terraform plan` and read it. It creates resources but costs nothing to run.
4. Run `terraform apply`.

## How to destroy

```bash
terraform destroy
```

Then confirm in the Azure portal that the `gateway-rg` resource group is gone. A `LoadBalancer` Service creates a public IP that Kubernetes owns rather than Terraform, so deleting the Service before destroying is the tidier order. If anything is left behind, deleting the resource group removes it.
