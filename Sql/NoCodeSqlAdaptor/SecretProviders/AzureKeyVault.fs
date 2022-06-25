module SecretProviders.AzureKeyVault

open System
open Azure.Identity
open Azure.Security.KeyVault.Secrets
open DotEnv

let tryInit () =
  let uriOption = getEnvironmentVariableOption "azurekeyvaulturi"
  let clientIdOption = getEnvironmentVariableOption "azurekeyvaultclientid"
  let clientSecretOption = getEnvironmentVariableOption "azurekeyvaultclientsecret"
  let tenantIdOption = getEnvironmentVariableOption "azurekeyvaulttenantid"
  match uriOption,clientIdOption, clientSecretOption, tenantIdOption with
  | Some uri, Some clientId, Some clientSecret, Some tenantId ->
    if String.IsNullOrWhiteSpace uri then
      None
    else
      SecretClient(vaultUri=Uri(uri), credential=ClientSecretCredential(tenantId, clientId, clientSecret)) |> Some
  | Some uri, _, _, _ ->
    if String.IsNullOrWhiteSpace uri then
      None
    else 
      SecretClient(vaultUri=Uri(uri), credential=ManagedIdentityCredential()) |> Some
  | _ -> None

let getSecret (secretClient:SecretClient) name = async {
  try
    let! response = (secretClient.GetSecretAsync name) |> Async.AwaitTask
    return response.Value.Value |> Ok
  with
  | :? System.AggregateException as exn ->
    let errors =
      exn.InnerExceptions
      |> Seq.map(fun innerExn -> $"{innerExn.Message}\n")
      |> String.Concat
    return Error $"Error retrieving Azure Key Vault secret named {name}:\n{errors}"
  | exn -> return Error $"Error retrieving Azure Key Vault secret named {name}: {exn.Message}"
}
