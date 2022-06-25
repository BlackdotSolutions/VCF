open Amazon.CDK
open Amazon.CDK.AWS.EKS
open AwsEcsDeploy

[<EntryPoint>]
let main _ =
    let app = App(null)
    let env = Environment (
        Account = "your-account",
        Region = "your-region"
      )

    AwsEcsDeployStack(
      app,
      "AwsEcsDeployStack",
      StackProps(
        Env=env
      )
    ) |> ignore

    app.Synth() |> ignore
    0
