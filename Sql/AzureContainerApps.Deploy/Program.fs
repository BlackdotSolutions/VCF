open Argu
open Argu.ArguAttributes
open Farmer
open Farmer.Builders
open Farmer.Arm

// get from cli arguments
let containerRegistryResourceId = "your-registry"
let containerRegistryDomain = "your-registry.azurecr.io"
let resourceGroup = "nocodesqladaptor"
let azureKeyVaultClientSecret = "your-keyvault-secret"

type CliArguments =
  | [<Mandatory>] ContainerAppPrefix of name:string
  | [<Mandatory>] ContainerRegistryResourceId of resourceId:string
  | ContainerRegistryDomain of domain:string
  | [<Mandatory>] ResourceGroup of resourceGroup:string
  | Location of location:string
  | AzureKeyVaultClientUri of uri:string
  | AzureKeyVaultClientSecret of secret:string
  | AzureKeyVaultClientId of clientId:string
  | AzureKeyVaultTenantId of tenantId:string
  | ConfigUri of uri:string
  interface IArgParserTemplate with
    member p.Usage =
      match p with
      | ContainerAppPrefix _ -> "Container app resources will be deployed prefixed with this name"
      | ContainerRegistryResourceId _ -> "The ID of the container registry with the docker container"
      | ContainerRegistryDomain _ -> "The domain of the container registry, if unspecified then this will default to {containerRegistryResourceId}.azurecr.io"
      | ResourceGroup _ -> "The resource group to deploy into or create"
      | Location _ -> "The location to deploy the assets to, defaults to North Europe"
      | AzureKeyVaultClientUri _ -> "The URI of a key vault to use for secrets, if specified either then the credentials must also be specified"
      | AzureKeyVaultClientId _ -> "The client ID of the key vault if key vault is to be used (if specified then the secret and tenant options must also be specified"
      | AzureKeyVaultClientSecret _ -> "The secret of the key vault"
      | AzureKeyVaultTenantId _ -> "The tenant ID of the key vault"
      | ConfigUri _ -> "An endpoint at which a configuration file can be located (e.g. a blob secured with a shared access signature)"

[<EntryPoint>]
let main args =
  
  let parser = ArgumentParser.Create<CliArguments> ()
  match args.Length with
  | 0 ->
    System.Console.Write (parser.PrintUsage ())    
  | _ ->
    let cliResults = parser.Parse args
    let prefix = cliResults.GetResult ContainerAppPrefix // nocodesqladaptor
    let containerRegistryResourceId = cliResults.GetResult ContainerRegistryResourceId // nocodesqladaptorregistry
    let containerRegistryDomain =
      defaultArg
        (cliResults.TryGetResult ContainerRegistryDomain)
        $"{containerRegistryResourceId}.azurecr.io"
    
    let adaptorContainerApp =
      containerEnvironment {
        name $"{prefix}-env"
        add_containers [
          containerApp {
            name $"{prefix}-app"
            reference_registry_credentials [
              ContainerRegistry.registries.resourceId containerRegistryResourceId
            ]
            add_containers [
              container {
                name $"{prefix}-container"
                private_docker_image containerRegistryDomain $"{prefix}-image" "latest"
                memory 1.0<Gb>
                cpu_cores 0.5<VCores>
              }
            ]
            ingress_target_port 80us
            ingress_transport ContainerApp.Transport.Auto
            add_env_variable "configuri" (defaultArg (cliResults.TryGetResult ConfigUri) "")  //"https://nocodesqladaptor.blob.core.windows.net/configuration/config.json?sv=2020-08-04&st=2022-03-16T08%3A31%3A39Z&se=2023-03-17T08%3A31%3A00Z&sr=b&sp=r&sig=7D8QQBpRBksgf1FRNzV3GdLYNWnf1kE1HkhGoqPLrtc%3D"
            add_env_variable "azurekeyvaulturi" (defaultArg (cliResults.TryGetResult AzureKeyVaultClientUri) "") // https://demonocodesqlkv.vault.azure.net/
            add_env_variable "azurekeyvaulttenantid" (defaultArg (cliResults.TryGetResult AzureKeyVaultTenantId) "") //"6c88a2fd-8551-4dc6-9400-ba4276370d69"
            add_env_variable "azurekeyvaultclientid" (defaultArg (cliResults.TryGetResult AzureKeyVaultClientId) "") //"529a23ec-cec5-45ef-be88-da04778f2bd6"
            // Their looks to be an issue with secret references in the preview or in the Farmer implementation so
            // temporarily adding as an environment variable but ought to be a secret
            add_env_variable "azurekeyvaultclientsecret" (defaultArg (cliResults.TryGetResult AzureKeyVaultClientSecret) "")  //"DBcUe.FR-I1Sl6ZkEl7gaOg~0i.bYfxB6n"        
            //add_secret_parameter "azurekeyvaultclientsecret"
          }
        ]
    }

    let deployment = arm {
      location (defaultArg (cliResults.TryGetResult CliArguments.Location |> Option.map Farmer.Location) Location.NorthEurope)
      add_resource adaptorContainerApp
    }

    deployment
    |> Deploy.execute resourceGroup Deploy.NoParameters
    |> ignore
    
    // When secrets are working the below should be used to deploy
    (*
    deployment
    |> Deploy.execute resourceGroup [ "azurekeyvaultclientsecret", azureKeyVaultClientSecret ]
    |> ignore
    *)
  
  0