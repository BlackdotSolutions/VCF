#az login --tenant 6c88a2fd-8551-4dc6-9400-ba4276370d69
#
#az extension add --source https://workerappscliextension.blob.core.windows.net/azure-cli-extension/containerapp-0.2.0-py2.py3-none-any.whl
#az provider register --namespace Microsoft.Web

az account set --subscription "5010c85f-eb8d-4cc4-8dac-8953ef5d3b8a"

RESOURCE_GROUP="nocodesqladaptor"
LOCATION="northeurope"
LOG_ANALYTICS_WORKSPACE="nocodesqladaptor-logs"
CONTAINERAPPS_ENVIRONMENT="nocodesqladaptor-env"
ACR="nocodesqladaptorregistry"

ACRTOKEN=$(az acr login --name $ACR --expose-token --output tsv --query accessToken)
docker login $ACR.azurecr.io --username 00000000-0000-0000-0000-000000000000 --password $ACRTOKEN

docker build -t nocodesqladaptor-image -f Dockerfile .
# The below will build on a M1 Mac but their is an issue with QEMU that many people are having, me included,
# which means that it won't actually build
#docker buildx build --platform linux/amd64  -t nocodesqladaptor-image -f Dockerfile .
docker image tag nocodesqladaptor-image $ACR.azurecr.io/nocodesqladaptor-image:latest
docker image push $ACR.azurecr.io/nocodesqladaptor-image:latest

az containerapp update \
  --name nocodesqladaptor-app \
  --resource-group $RESOURCE_GROUP \
  --image $ACR.azurecr.io/nocodesqladaptor-image:latest \
  --registry-login-server $ACR.azurecr.io \
  --registry-username $ACRUSERNAME \
  --registry-password $ACRPASSWORD \
  --query configuration.ingress.fqdn