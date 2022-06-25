module SecretProviders.Default

let getSecret name = async {
  return Error "No secret manager configured. Required for templated connection strings."
}