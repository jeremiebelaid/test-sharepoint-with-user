
build-aci-image:
	@echo "Authentification à Azure Container Registry..."
	docker login $(ACR_NAME).azurecr.io --username $(ACR_USERNAME) --password $(ACR_PASSWORD)

	@echo "Construction de l'image Docker pour ACI de développement..."
	docker build -t $(ACR_NAME).azurecr.io/aci-dev:latest .

	@echo "Poussée de l'image vers Azure Container Registry..."
	docker push $(ACR_NAME).azurecr.io/aci-dev:latest

