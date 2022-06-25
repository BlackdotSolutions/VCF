module Api
open System
open ApiTypes
open Giraffe.HttpStatusCodeHandlers
open Microsoft.AspNetCore.Http
open Thoth.Json.Giraffe
open Thoth.Json.Net
open Giraffe
open Configuration
open Query
open Saturn

let private customMapEncoder (value:Map<AttributeType,string>) =
  Encode.object (
    value
    |> Seq.map(fun kvp ->
      (kvp.Key.ToString(), Encode.string kvp.Value)
    )
    |> Seq.toList
  )
let private customMapDecoder value = raise (NotSupportedException("Attribute map decoding note supported"))

let implementation configuration apiTokenOption =
  let getSearchResults searcherId =
    configuration.Connections
    |> List.tryFind(fun connection -> connection.Id = searcherId)
    |> (function
      | Some connection ->
        fun (next: HttpFunc) (ctx: HttpContext) -> task {
          match ctx.TryGetQueryStringValue "query" with
          | Some query ->
            let maxResults =
              (ctx.TryGetQueryStringValue "maxResults")
            |> Option.map(fun v -> v |> Int32.Parse)
            |> Option.defaultValue 200
            let! searchResults = executeQuery connection maxResults query
            return!
              ThothSerializer.RespondJson
                searchResults
                (Encode.Auto.generateEncoder
                  (CaseStrategy.CamelCase,extra=(Extra.empty |> Extra.withCustom customMapEncoder customMapDecoder))
                )
                next
                ctx 
          | None -> return! RequestErrors.BAD_REQUEST "Query required" next ctx
        }
      | None -> RequestErrors.BAD_REQUEST "Searcher not found"
    )
  
  let authenticate =
    match apiTokenOption with
    | Some _ ->
      requiresAuthentication (Giraffe.Auth.challenge NoCodeSqlAdaptor.ApiTokenAuthentication.AuthenticationScheme)
    | None -> id
  
  GET >=>
    choose [
      subRoute "/searchers" (authenticate >=> choose [
        route "" >=> (configuration |> searchers |> json)
        route "/" >=> (configuration |> searchers |> json)
        routef "/%s/results" getSearchResults
      ])
      route "/version" >=> ("0.1.1" |> text)
      route "/" >=> ("NoCodeSqlAdaptor" |> text) // root response needed for ECS health check
      RequestErrors.NOT_FOUND "Not Found"
    ]
    
  
  

