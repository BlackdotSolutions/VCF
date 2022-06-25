module NoCodeSqlAdaptor.ApiTokenAuthentication

open System.Security.Claims
open Microsoft.AspNetCore.Authentication
open Microsoft.AspNetCore.Builder
open Microsoft.Extensions.DependencyInjection
open Saturn

let AuthenticationScheme = "ApiTokenAuthentication"

type ApiTokenProvider(apiTokenOption) =
  member this.apiTokenOption = apiTokenOption
  
type ApiTokenAuthHandler(options, logger, encoder, clock, apiTokenProvider : ApiTokenProvider) =
  inherit AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder, clock)
  override this.HandleAuthenticateAsync() =
    let createTicket nameIdentifier =
      let claims = [| Claim(ClaimTypes.NameIdentifier, nameIdentifier) |]
      let identity = ClaimsIdentity(claims, this.Scheme.Name)
      let principal = ClaimsPrincipal identity
      AuthenticationTicket(principal, this.Scheme.Name)
    
    match apiTokenProvider.apiTokenOption with
    | Some apiToken ->
      match this.Request.Query.TryGetValue "apiToken" with
      | true,queryParameterValue ->
        if apiToken <> queryParameterValue.[0] then
          task { return AuthenticateResult.Fail "Not Implemented" }
        else
          task { return AuthenticateResult.Success (createTicket apiToken) }
      | false,_ ->
        task { return AuthenticateResult.Fail "API token required" }
    | None ->
      task { return AuthenticateResult.Success (createTicket "anonymous") }

type ApplicationBuilder with
  [<CustomOperation("use_apitoken_auth")>]
  member __.UseApiTokenAuth(state : ApplicationState, apiTokenOption: string option) =
    let middleware (app : IApplicationBuilder) =
      app.UseAuthentication()

    let service (s : IServiceCollection) =
      s.AddAuthentication(AuthenticationScheme)
        .AddScheme<AuthenticationSchemeOptions, ApiTokenAuthHandler>(AuthenticationScheme, null)
        |> ignore
      s.AddSingleton(ApiTokenProvider(apiTokenOption)) |> ignore
      s

    { state with
        ServicesConfig = service::state.ServicesConfig
        AppConfigs = middleware::state.AppConfigs }

