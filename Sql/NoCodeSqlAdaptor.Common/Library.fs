module NoCodeSqlAdaptor.Common
open FsHttp.DslCE
open FsHttp.Response
open System.Text.RegularExpressions

let tokenRegexPrefix = "\{\!"
let tokenRegexPostfix = "\!\}"
let tokenRegex = $"{tokenRegexPrefix}(.*?){tokenRegexPostfix}"

let extractTokens inString =
  Regex.Matches (inString,tokenRegex)
  |> Seq.map (fun regexMatch ->
    if regexMatch.Groups.Count = 2 then
      regexMatch.Groups.[1].Value
    else
      ""
  )
  |> Seq.filter (System.String.IsNullOrWhiteSpace >> not)
  |> Seq.toList

let getConfigurationText relativePath configUriOption = async {
  try
    return!
      match configUriOption with
      | Some configUri -> async {
          try
            let! response = httpAsync { GET configUri }
            let! loadedConfig = response |> toTextAsync
            return Ok loadedConfig
          with
          | exn -> return Error $"Unable to load config from URI: {exn.Message}"
        }
      | None -> async { 
          let! text = System.IO.File.ReadAllTextAsync $"{relativePath}config.json" |> Async.AwaitTask
          return Ok text
        }
  with
  | exn ->
    return Error $"Unable to load config with error: {exn.Message}"
}

