module Configuration
open System.Text.RegularExpressions
open ApiTypes
open FsToolkit.ErrorHandling
open Thoth.Json.Net
open NoCodeSqlAdaptor.Common

exception BadConfiguration of string
exception ApiTokenSecretNotFoundException of string

module Array =
  let asyncToList (v:Async<'a[]>) = async {
    let! a = v
    return a |> Array.toList
  }

[<RequireQualifiedAccess>]
type DatabaseType =
  | SQLServer
  | SQLServerFullText
  | Postgres
  
type SearchColumn =
  { Name: string
    Weight: float option
  }
  
type EntityAttributeMapping =
  { FromColumn: string
    ToAttribute: AttributeType
  }
  
type EntityDefinition =
  { EntityType: EntityType
    EntityAttributes: EntityAttributeMapping list
  }
  
type SearchEntity =
  { Name: string
    Key: string option
    Title: string
    Source: string
    ScoreBasedOnMatchCount: bool option
    SearchColumns: SearchColumn list option
    EntityDefinition: EntityDefinition option
  }

type Connection =
  { Id: string
    // We'd want to allow passwords / secrets to be tokenised and inserted at runtime through a registered provider
    // e.g. a key vault
    ConnectionString: string
    Name: string
    ServerType: DatabaseType
    Entities: SearchEntity list
    Hint: string option
    Tooltip: string option
  }

type Config =
  { Connections: Connection list
  }
  
let getApiToken getSecret : Async<string option> = async {
  return!
    match DotEnv.getEnvironmentVariableOption "apitokensecretname" with
    | Some apiTokenSecretName -> async {
        let! apiTokenResult = getSecret apiTokenSecretName
        return
          match apiTokenResult with
          | Ok apiToken -> Some apiToken
          | Error e -> raise (ApiTokenSecretNotFoundException $"API token with secret name of {apiTokenSecretName} could not be found in the secret provider")
      }    
    | None -> async {
      return DotEnv.getEnvironmentVariableOption "apitoken"
    }
}
  
let loadConfiguration getSecret : Async<Result<Config,string>> = async {
  try
    let replaceTokens (inString:string) (tokenValuePairs:(string*string) list) =
      tokenValuePairs
      |> List.fold (fun updatedString (token,value) ->
        let replaceRegex = $"{tokenRegexPrefix}({token}){tokenRegexPostfix}"
        Regex.Replace (updatedString, replaceRegex, value)
      ) inString
      
    let pairTokensWithValues tokens = async {
      let! pairs =
        tokens
        |> List.map (fun token -> async {
          let! secret = getSecret token
          return secret |> Result.map (fun s -> (token,s))
        })
        |> Async.Parallel
      return pairs |> Array.toList |> List.sequenceResultM
    }
    
    let configUriOption = DotEnv.getEnvironmentVariableOption "configuri"
    let! configurationTextResult = getConfigurationText "./" configUriOption
    match configurationTextResult with
    | Ok configurationText ->
      let decodedConfigResult = Decode.Auto.fromString<Config> (configurationText, caseStrategy=CaseStrategy.CamelCase) 
      let! updatedConfig =
        match decodedConfigResult with
        | Ok decodedConfig -> async {
            let! updatedConnections =
              decodedConfig.Connections
              |> List.map(fun connection -> async {
                let! tokensAndValueResult = connection.ConnectionString |> extractTokens |> pairTokensWithValues
                return
                  (
                   tokensAndValueResult
                   |> Result.map (replaceTokens connection.ConnectionString)
                   |> Result.map (fun connectionString -> { connection with ConnectionString = connectionString })
                  )
              })
              |> Async.Parallel
              
            return
              updatedConnections
              |> Array.toList
              |> List.sequenceResultM
              |> Result.map (fun okResult -> { decodedConfig with Connections = okResult })
          }
        | Error e -> async { return Error e }
      return updatedConfig
    | Error e -> return Error e
  with
  | exn ->
    return Error exn.Message
}

let searchers config =
  config.Connections
  |> List.map(fun connection -> {
    Id = connection.Id
    Name = connection.Name
    Hint = connection.Hint
    Tooltip = connection.Tooltip
  })
