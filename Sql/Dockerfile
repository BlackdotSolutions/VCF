# We're forcing the platform to AMD64 here to support building on an M1 Mac and targetting Intel/AMD cloud compute
FROM --platform=linux/amd64 mcr.microsoft.com/dotnet/aspnet:6.0 AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY ["./NoCodeSqlAdaptor.Common/*", "NoCodeSqlAdaptor.Common/"]
COPY ["./NoCodeSqlAdaptor/*", "NoCodeSqlAdaptor/"]
COPY ["./NoCodeSqlAdaptor/SecretProviders/*", "NoCodeSqlAdaptor/SecretProviders/"]
WORKDIR /src/NoCodeSqlAdaptor
RUN dotnet restore "NoCodeSqlAdaptor.fsproj"
RUN dotnet build "NoCodeSqlAdaptor.fsproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "NoCodeSqlAdaptor.fsproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "NoCodeSqlAdaptor.dll"]
