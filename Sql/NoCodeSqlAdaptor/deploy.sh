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

az group create \
  --name $RESOURCE_GROUP \
  --location "$LOCATION"

az acr create -n $ACR -g $RESOURCE_GROUP --sku Standard
az acr update -n $ACR --admin-enabled true

ACRUSERNAME=$(az acr credential show -n $ACR --query username)
ACRUSERNAME="${ACRUSERNAME:1: -1}"
ACRPASSWORD=$(az acr credential show -n $ACR --query "passwords[0].value")
ACRPASSWORD="${ACRPASSWORD:1: -1}"

ACRTOKEN=$(az acr login --name $ACR --expose-token --output tsv --query accessToken)
docker login $ACR.azurecr.io --username 00000000-0000-0000-0000-000000000000 --password $ACRTOKEN

docker build -t nocodesqladaptor-image -f Dockerfile .
# The below will build on a M1 Mac but their is an issue with QEMU that many people are having, me included,
# which means that it won't actually build
#docker buildx build --platform linux/amd64  -t nocodesqladaptor-image -f Dockerfile .
docker image tag nocodesqladaptor-image $ACR.azurecr.io/nocodesqladaptor-image:latest
docker image push $ACR.azurecr.io/nocodesqladaptor-image:latest

: <<'END'
az containerapp update \
  --name nocodesqladaptor-app \
  --resource-group $RESOURCE_GROUP \
  --image $ACR.azurecr.io/nocodesqladaptor-image:latest \
  --registry-login-server $ACR.azurecr.io \
  --registry-username $ACRUSERNAME \
  --registry-password $ACRPASSWORD \
  --environment-variables configUri=secretref:configuri,azureKeyVaultUri=https://demonocodesqlkv.vault.azure.net/,azureKeyVaultTenantId=6c88a2fd-8551-4dc6-9400-ba4276370d69,azureKeyVaultClientId=529a23ec-cec5-45ef-be88-da04778f2bd6,azureKeyVaultClientSecret=DBcUe.FR-I1Sl6ZkEl7gaOg~0i.bYfxB6n
END

: <<'END'
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE

LOG_ANALYTICS_WORKSPACE_CLIENT_ID=`az monitor log-analytics workspace show --query customerId -g $RESOURCE_GROUP -n $LOG_ANALYTICS_WORKSPACE --out tsv`

LOG_ANALYTICS_WORKSPACE_CLIENT_SECRET=`az monitor log-analytics workspace get-shared-keys --query primarySharedKey -g $RESOURCE_GROUP -n $LOG_ANALYTICS_WORKSPACE --out tsv`

az containerapp env create \
  --name $CONTAINERAPPS_ENVIRONMENT \
  --resource-group $RESOURCE_GROUP \
  --logs-workspace-id $LOG_ANALYTICS_WORKSPACE_CLIENT_ID \
  --logs-workspace-key $LOG_ANALYTICS_WORKSPACE_CLIENT_SECRET \
  --location "$LOCATION"

#--min-replicas 1 \

az containerapp create \
  --name nocodesqladaptor-app \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENVIRONMENT \
  --image $ACR.azurecr.io/nocodesqladaptor-image:latest \
  --target-port 80 \
  --ingress 'external' \
  --memory 2.0Gi \
  --cpu 1 \
  --registry-login-server $ACR.azurecr.io \
  --registry-username $ACRUSERNAME \
  --registry-password $ACRPASSWORD \
  --query configuration.ingress.fqdn \
  --environment-variables configUri=secretref:configuri,azureKeyVaultUri=https://demonocodesqlkv.vault.azure.net/,azureKeyVaultTenantId=6c88a2fd-8551-4dc6-9400-ba4276370d69,azureKeyVaultClientId=529a23ec-cec5-45ef-be88-da04778f2bd6,azureKeyVaultClientSecret=DBcUe.FR-I1Sl6ZkEl7gaOg~0i.bYfxB6n

END