namespace AwsEcsDeploy

open System
open Amazon.CDK
open Amazon.CDK.AWS.CertificateManager
open Amazon.CDK.AWS.EC2
open Amazon.CDK.AWS.ECS
open Amazon.CDK.AWS.ECS.Patterns
open Amazon.CDK.AWS
open DotEnv

exception ConfigurationFileNotFoundException

type AwsEcsDeployStack(scope, id, props) as this =
    inherit Stack(scope, id, props)
    let defaultConsoleColor = Console.ForegroundColor
    let unspecified = null // CDK uses null for unspecified properties, just making it a bit more F#y
    let configUriOption = getEnvironmentVariableOption "ncsa_configuri"
    let configUri = defaultArg configUriOption ""
    let domainOption = getEnvironmentVariableOption "ncsa_domain"
    let subDomainOption = getEnvironmentVariableOption "ncsa_subdomain"
    let hostedZoneName =
      match getEnvironmentVariableOption "ncsa_hostedzone" with
      | Some hostedZone -> Some hostedZone
      | None -> domainOption
    
    let supportHttps,fullyQualifiedDomainName,domain =
      match domainOption,subDomainOption with
      | Some domain, Some subDomain -> true,$"{domain}.{subDomain}",domain
      | _ -> false,unspecified,unspecified
    do
      if supportHttps then
        Console.ForegroundColor <- ConsoleColor.Red
        Console.WriteLine($"Configuring with https for {fullyQualifiedDomainName}")
        Console.ForegroundColor <- defaultConsoleColor
    
    let configurationFileResult =
      NoCodeSqlAdaptor.Common.getConfigurationText "../NoCodeSqlAdaptor/" configUriOption |> Async.RunSynchronously
    let secrets =
      match configurationFileResult with
      | Ok configurationFile ->
        // Passing the whole JSON in here to save deserializing into the model - if this doesn't hold up in practice
        // we can go for the deserialization approach but it involves making more of the config common
        configurationFile
        |> NoCodeSqlAdaptor.Common.extractTokens
        |> List.distinct
        |> List.mapi(fun i secretName ->
          Console.ForegroundColor <- ConsoleColor.Yellow
          Console.WriteLine $"Found and configuring secret {secretName}"
          Console.ForegroundColor <- defaultConsoleColor
          SecretsManager.Secret.FromSecretNameV2(this, $"Secret{i}", secretName)
        )
      | Error e ->
        Console.ForegroundColor <- ConsoleColor.Red
        Console.WriteLine e
        Console.ForegroundColor <- defaultConsoleColor
        raise ConfigurationFileNotFoundException
    
    let vpc = Vpc (this, "NoCodeSqlAdaptorVpc", VpcProps(MaxAzs = 3.))
    let cluster = Cluster (this, "NoCodeSqlAdaptorCluster", ClusterProps(Vpc = vpc))
    
    let taskRole =
      IAM.Role(
        this,
        "NoCodeSqlAdaptorTaskRole",
        IAM.RoleProps(AssumedBy = IAM.ServicePrincipal("ecs-tasks.amazonaws.com"))
      )
    do
      secrets
      |> List.iter(fun secret -> secret.GrantRead taskRole |> ignore)
    
    // To expose on HTTPS you will need a domain name registered with Route53
    // and then uncomment the below block - this will register a certificate for
    // your endpoint and validate it using Route53
    let domainZone =
      if supportHttps then
        Route53.HostedZone.FromLookup(
          this,
          hostedZoneName.Value,
          Route53.HostedZoneProviderProps(DomainName=domain)
        )
      else
        unspecified
    let apiCertificate =
      if supportHttps then
        Certificate(
          this,
          "NoCodeSqlAdaptorCertificate",
          CertificateProps(
            DomainName = fullyQualifiedDomainName,
            Validation = CertificateValidation.FromDns(domainZone)
          )
        )
      else
        unspecified
    
    let service =
      ApplicationLoadBalancedFargateService (
        this,
        "NoCodeSqlAdaptorFargateService",
        ApplicationLoadBalancedFargateServiceProps(
          Cluster = cluster,
          DesiredCount = 1.,
          TaskImageOptions = ApplicationLoadBalancedTaskImageOptions(
            Image = ContainerImage.FromAsset("../"),
            Environment = ([
              "configuri", configUri
              "awssecretmanager","true"
            ] |> Map.ofList),
            TaskRole = taskRole
          ),
          MemoryLimitMiB = 1024.,
          PublicLoadBalancer = true,
          // To expose an HTTPS endpoint you will need a domain name and a corresponding certificate (see earlier code)
          // and then uncomment the below
          Certificate = apiCertificate,
          DomainName = fullyQualifiedDomainName,
          DomainZone = domainZone
        )
      ) 
      
    do CfnOutput(this, "publicEndpoint", CfnOutputProps(ExportName=("PublicEndpoint"), Value=service.LoadBalancer.LoadBalancerDnsName )) |> ignore
    
   