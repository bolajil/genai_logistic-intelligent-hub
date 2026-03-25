# GLIH - Makefile for Development and Deployment

.PHONY: dev test build push deploy-aws deploy-gcp deploy-azure stop logs clean

# ============================================================
# Development
# ============================================================

dev:
	docker-compose up -d
	@echo "GLIH running at http://localhost:9000"
	@echo "Backend API at http://localhost:9001"

dev-build:
	docker-compose up -d --build

stop:
	docker-compose down

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# ============================================================
# Testing
# ============================================================

test:
	cd glih-backend && python -m pytest tests/ -v
	cd glih-frontend-next && npm run lint

test-load:
	@echo "Load testing not yet configured"

# ============================================================
# Build
# ============================================================

build:
	docker build -t glih-backend:latest ./glih-backend
	docker build -t glih-frontend:latest ./glih-frontend-next

# ============================================================
# AWS Deployment
# ============================================================

deploy-aws-init:
	cd deploy/aws && terraform init

deploy-aws-plan:
	cd deploy/aws && terraform plan -var-file=terraform.tfvars

deploy-aws:
	@echo "=== AWS Deployment ==="
	@echo "1. Building and pushing images to ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker tag glih-backend:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/glih-backend:latest
	docker tag glih-frontend:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/glih-frontend:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/glih-backend:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/glih-frontend:latest
	@echo "2. Applying Terraform..."
	cd deploy/aws && terraform apply -var-file=terraform.tfvars
	@echo "3. Applying Kubernetes manifests..."
	kubectl apply -f deploy/k8s/namespace.yaml
	kubectl apply -f deploy/k8s/configmap.yaml
	kubectl apply -f deploy/k8s/secrets.yaml
	kubectl apply -f deploy/k8s/pvc.yaml
	kubectl apply -f deploy/k8s/backend-deployment.yaml
	kubectl apply -f deploy/k8s/frontend-deployment.yaml
	kubectl apply -f deploy/k8s/ingress.yaml
	@echo "=== AWS Deployment Complete ==="

# ============================================================
# GCP Deployment
# ============================================================

deploy-gcp-init:
	cd deploy/gcp && terraform init

deploy-gcp-plan:
	cd deploy/gcp && terraform plan -var-file=terraform.tfvars

deploy-gcp:
	@echo "=== GCP Deployment ==="
	@echo "1. Building and pushing images to Artifact Registry..."
	gcloud auth configure-docker $(GCP_REGION)-docker.pkg.dev
	docker tag glih-backend:latest $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/glih-images/glih-backend:latest
	docker tag glih-frontend:latest $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/glih-images/glih-frontend:latest
	docker push $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/glih-images/glih-backend:latest
	docker push $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/glih-images/glih-frontend:latest
	@echo "2. Applying Terraform..."
	cd deploy/gcp && terraform apply -var-file=terraform.tfvars
	@echo "3. Getting GKE credentials..."
	gcloud container clusters get-credentials glih-gke --region $(GCP_REGION) --project $(GCP_PROJECT)
	@echo "4. Applying Kubernetes manifests..."
	kubectl apply -f deploy/k8s/namespace.yaml
	kubectl apply -f deploy/k8s/configmap.yaml
	kubectl apply -f deploy/k8s/secrets.yaml
	kubectl apply -f deploy/k8s/pvc.yaml
	kubectl apply -f deploy/k8s/backend-deployment.yaml
	kubectl apply -f deploy/k8s/frontend-deployment.yaml
	kubectl apply -f deploy/k8s/ingress.yaml
	@echo "=== GCP Deployment Complete ==="

# ============================================================
# Azure Deployment
# ============================================================

deploy-azure-init:
	cd deploy/azure && terraform init

deploy-azure-plan:
	cd deploy/azure && terraform plan -var-file=terraform.tfvars

deploy-azure:
	@echo "=== Azure Deployment ==="
	@echo "1. Building and pushing images to ACR..."
	az acr login --name $(AZURE_ACR_NAME)
	docker tag glih-backend:latest $(AZURE_ACR_NAME).azurecr.io/glih-backend:latest
	docker tag glih-frontend:latest $(AZURE_ACR_NAME).azurecr.io/glih-frontend:latest
	docker push $(AZURE_ACR_NAME).azurecr.io/glih-backend:latest
	docker push $(AZURE_ACR_NAME).azurecr.io/glih-frontend:latest
	@echo "2. Applying Terraform..."
	cd deploy/azure && terraform apply -var-file=terraform.tfvars
	@echo "3. Getting AKS credentials..."
	az aks get-credentials --resource-group glih-production --name glih-aks
	@echo "4. Applying Kubernetes manifests..."
	kubectl apply -f deploy/k8s/namespace.yaml
	kubectl apply -f deploy/k8s/configmap.yaml
	kubectl apply -f deploy/k8s/secrets.yaml
	kubectl apply -f deploy/k8s/pvc.yaml
	kubectl apply -f deploy/k8s/backend-deployment.yaml
	kubectl apply -f deploy/k8s/frontend-deployment.yaml
	kubectl apply -f deploy/k8s/ingress.yaml
	@echo "=== Azure Deployment Complete ==="

# ============================================================
# Cleanup
# ============================================================

clean:
	docker-compose down -v
	docker system prune -f

destroy-aws:
	cd deploy/aws && terraform destroy -var-file=terraform.tfvars

destroy-gcp:
	cd deploy/gcp && terraform destroy -var-file=terraform.tfvars

destroy-azure:
	cd deploy/azure && terraform destroy -var-file=terraform.tfvars
