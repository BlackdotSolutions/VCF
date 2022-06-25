module SecretProviders.AwsSecretManager

open System
open Amazon
open Amazon.SecretsManager
open Amazon.SecretsManager.Model
open DotEnv

let tryInit () =
  let awsSecretManagerOption = getEnvironmentVariableOption "awssecretmanager"
  let awsSecretManagerRegionOption = getEnvironmentVariableOption "awssecretmanagerregion"
  
  match awsSecretManagerOption, awsSecretManagerRegionOption with
  | _, Some region ->
    let config = AmazonSecretsManagerConfig(RegionEndpoint = RegionEndpoint.GetBySystemName(region))
    Some (new AmazonSecretsManagerClient(config))
  | Some _, None ->
    let config = AmazonSecretsManagerConfig()
    Some (new AmazonSecretsManagerClient(config))
  | None, None ->
    None

let getSecret (secretClient:AmazonSecretsManagerClient) name = async {
  try
    let request = GetSecretValueRequest(SecretId = name)
    let! response = secretClient.GetSecretValueAsync request |> Async.AwaitTask
    return response.SecretString |> Ok
  with
  | exn -> return Error $"Error retrieving AWS Secret Manager secret named {name}: {exn.Message}"
}
