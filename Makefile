
build:
	@echo "Authentification à Azure Container Registry..."
	docker login $(ACR_NAME).azurecr.io --username $(ACR_USERNAME) --password $(ACR_PASSWORD)

	@echo "Construction de l'image Docker pour ACI de développement..."
	docker build \
		-f docker/Dockerfile \
		--progress=plain \
		--secret id=dev_password,env=DEVELOPER_PASSWORD \
		--secret id=dev_ssh_public_key,env=DEVELOPER_SSH_PUBLIC_KEY \
		-t $(ACR_NAME).azurecr.io/aci-dev:latest .

	@echo "Poussée de l'image vers Azure Container Registry..."
	docker push $(ACR_NAME).azurecr.io/aci-dev:latest

