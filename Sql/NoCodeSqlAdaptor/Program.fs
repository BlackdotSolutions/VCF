module Entry
open System
open Microsoft.AspNetCore.Http
open Spectre.Console.FSharp
open Giraffe
open Configuration
open Microsoft.Extensions.Logging
open Saturn
open NoCodeSqlAdaptor.ApiTokenAuthentication

module Option =
  let whenNone fn optionValue =
    match optionValue with
    | Some value -> Some value
    | None -> fn ()

let richStartupError title error =
  render (Widget.Text [ TextProp.Text $"{title}\n" ; TextProp.TextStyle [ TextStyle.Bold ; TextStyle.ForegroundColor Red ] ])
  render (Widget.Text [ TextProp.Text $"{error}\n" ; TextProp.TextStyle [ TextStyle.ForegroundColor Red ] ])
let richStartupInfo info =
  render (Widget.Text [ TextProp.Text $"{info}\n" ; TextProp.TextStyle [ TextStyle.ForegroundColor Green ] ])

let secretProvider:string->Async<Result<string,string>> =
  SecretProviders.AwsSecretManager.tryInit()
  |> Option.map(fun secretClient -> SecretProviders.AwsSecretManager.getSecret secretClient)
  |> Option.whenNone(fun () ->
    SecretProviders.AzureKeyVault.tryInit ()
    |> Option.map (fun secretClient -> SecretProviders.AzureKeyVault.getSecret secretClient)
  )
  |> Option.defaultValue SecretProviders.Default.getSecret
  
let apiTokenOption = getApiToken secretProvider |> Async.RunSynchronously
if apiTokenOption.IsSome then richStartupInfo "API Token found - using authentication"

// We need to get the right secret provider based on the environment variables (see README.md)
match loadConfiguration secretProvider |> Async.RunSynchronously with
| Error e ->
  richStartupError "Error loading configuration" e
| Ok configuration ->
  richStartupInfo "Starting web server"
  let app = application {
    use_apitoken_auth apiTokenOption
    logging (fun builder -> builder.AddConsole().AddDebug() |> ignore)
    error_handler (fun ex logger ->
      logger.LogError(ex, "An unhandled exception {exceptionType} has occurred while executing the request.", ex.GetType().Name)
      clearResponse >=> setStatusCode 500 >=> text "Internal error"
    )
    use_router (Api.implementation configuration apiTokenOption)
    use_gzip
  }
  
  run app

