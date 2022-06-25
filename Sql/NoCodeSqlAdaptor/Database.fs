module SqlAccess

open System
open System.Data
open System.Data.Common
open System.Data.SqlClient
open System.Data.SqlTypes
open Npgsql
open NpgsqlTypes

type ColumnMismatchException(columnName, inner:InvalidCastException) =
  inherit exn ($"Cast error for column '%s{columnName}'.", inner)
  member _.ColumnName = columnName
type ColumnNullException(columnName, inner:SqlNullValueException) =
  inherit exn ($"Null value for column '%s{columnName}' when non-null expected.", inner)
  member _.ColumnName = columnName
type UnknownColumnException(columnName, inner:IndexOutOfRangeException) =
  inherit exn ($"No such column '%s{columnName}' exists.", inner)
  member _.ColumnName = columnName

type RowReader (reader:DbDataReader) =
  member val Reader = reader with get
  
  member inline private t.asMandatory mapper col =
    try
      t.Reader.GetOrdinal col |> mapper
    with
    | :? InvalidCastException as ex -> raise (ColumnMismatchException(col, ex))
    | :? IndexOutOfRangeException as ex -> raise (UnknownColumnException(col, ex))
    | :? SqlNullValueException as ex -> raise (ColumnNullException(col, ex))
  
  member inline private r.asOptional mapper col =
    try
      let index = r.Reader.GetOrdinal col
      if r.Reader.IsDBNull index then None else Some(mapper index)
    with
    | :? InvalidCastException as ex -> raise (ColumnMismatchException(col, ex))
    | :? IndexOutOfRangeException as ex -> raise (UnknownColumnException(col, ex))
    | :? SqlNullValueException as ex -> raise (ColumnNullException(col, ex))
    
  member r.char = r.asMandatory (r.Reader.GetString >> Seq.head)
  member r.charOption = r.asOptional (r.Reader.GetString >> Seq.head)
  member r.int = r.asMandatory r.Reader.GetInt32
  member r.intOption = r.asOptional r.Reader.GetInt32
  member r.int64 = r.asMandatory r.Reader.GetInt64
  member r.int64Option = r.asOptional r.Reader.GetInt64
  member r.decimal = r.asMandatory r.Reader.GetDecimal
  member r.decimalOption = r.asOptional r.Reader.GetDecimal
  member r.date = r.asMandatory r.Reader.GetDateTime
  member r.dateOption = r.asOptional r.Reader.GetDateTime
  member r.bool = r.asMandatory r.Reader.GetBoolean
  member r.boolOption = r.asOptional r.Reader.GetBoolean
  member r.float = r.asMandatory r.Reader.GetDouble
  member r.floatOption = r.asOptional r.Reader.GetDouble
  member r.guid = r.asMandatory r.Reader.GetGuid
  member r.guidOption = r.asOptional r.Reader.GetGuid
  member r.string = r.asMandatory r.Reader.GetString
  member r.stringOption = r.asOptional r.Reader.GetString

[<RequireQualifiedAccess>]
type SqlValueType<'a> =
  | Required of 'a
  | Optional of Option<'a>
  | List of 'a list

[<RequireQualifiedAccess>]
type SqlCommandParameterValue =
  | Uuid of SqlValueType<Guid>
  | String of SqlValueType<string>
  | DateTime of SqlValueType<System.DateTime>
  | Integer of SqlValueType<Int32>
  | Long of SqlValueType<Int64>
  | Float of SqlValueType<float>
  | Boolean of SqlValueType<bool>
  
type Parameter () =
  static member Value (value:Guid) = value |> SqlValueType.Required |> SqlCommandParameterValue.Uuid
  static member Value (value:Guid option) = value |> SqlValueType.Optional |> SqlCommandParameterValue.Uuid
  static member Value (value:Guid list) = value |> SqlValueType.List |> SqlCommandParameterValue.Uuid
  static member Value (value:string) = value |> SqlValueType.Required |> SqlCommandParameterValue.String
  static member Value (value:string option) = value |> SqlValueType.Optional |> SqlCommandParameterValue.String
  static member Value (value:string list) = value |> SqlValueType.List |> SqlCommandParameterValue.String
  static member Value (value:DateTime) = value |> SqlValueType.Required |> SqlCommandParameterValue.DateTime
  static member Value (value:DateTime option) = value |> SqlValueType.Optional |> SqlCommandParameterValue.DateTime
  static member Value (value:DateTime list) = value |> SqlValueType.List |> SqlCommandParameterValue.DateTime
  static member Value (value:int) = value |> SqlValueType.Required |> SqlCommandParameterValue.Integer
  static member Value (value:int option) = value |> SqlValueType.Optional |> SqlCommandParameterValue.Integer
  static member Value (value:int list) = value |> SqlValueType.List |> SqlCommandParameterValue.Integer
  static member Value (value:Int64) = value |> SqlValueType.Required |> SqlCommandParameterValue.Long
  static member Value (value:Int64 option) = value |> SqlValueType.Optional |> SqlCommandParameterValue.Long
  static member Value (value:Int64 list) = value |> SqlValueType.List |> SqlCommandParameterValue.Long 
  static member Value (value:float) = value |> SqlValueType.Required |> SqlCommandParameterValue.Float
  static member Value (value:float option) = value |> SqlValueType.Optional |> SqlCommandParameterValue.Float
  static member Value (value:float list) = value |> SqlValueType.List |> SqlCommandParameterValue.Float
  static member Value (value:bool) = value |> SqlValueType.Required |> SqlCommandParameterValue.Boolean
  static member Value (value:bool option) = value |> SqlValueType.Optional |> SqlCommandParameterValue.Boolean
  static member Value (value:bool list) = value |> SqlValueType.List |> SqlCommandParameterValue.Boolean
  
type ISql =
  abstract member TryFetchSingle : string -> (string * SqlCommandParameterValue) list -> (RowReader -> 'r) -> Async<'r option>
  abstract member FetchSingle : string -> (string * SqlCommandParameterValue) list -> (RowReader -> 'r) -> Async<'r>
  abstract member FetchMany : string -> (string * SqlCommandParameterValue) list -> (RowReader -> 'r) -> Async<'r list>
  abstract member ExecuteInt : string -> (string * SqlCommandParameterValue) list -> Async<int>
  abstract member Execute : string -> (string * SqlCommandParameterValue) list -> Async<unit>
  
     
let sql commandFactory parameterFactory connection =
  let fetchMany (sql:string) parameters (mapper:RowReader -> 'r) = async {
    let connectionSpecificParameters =
      parameters
      |> List.map(fun (name,value) -> parameterFactory name value)
      |> List.toArray
    use cmd:DbCommand = commandFactory sql connection
    cmd.Parameters.AddRange(connectionSpecificParameters)
    use! reader = cmd.ExecuteReaderAsync() |> Async.AwaitTask
    let results = [ while reader.Read() do mapper (RowReader(reader)) ]
    return results
  }
  
  let fetchSingle sql parameters mapper = async {
    let! results = fetchMany sql parameters mapper
    return results |> List.head
  }
  
  let tryFetchSingle sql parameters mapper = async {
    let! results = fetchMany sql parameters mapper
    return results |> List.tryHead
  }
  
  let executeInt (sql:string) parameters = async {
    let connectionSpecificParameters =
      parameters
      |> List.map(fun (name,value) -> parameterFactory name value)
      |> List.toArray
    use cmd:DbCommand = commandFactory sql connection
    cmd.Parameters.AddRange(connectionSpecificParameters)
    let! result = cmd.ExecuteNonQueryAsync() |> Async.AwaitTask    
    return result
  }
  
  let execute sql parameters = async {
    do! executeInt sql parameters |> Async.Ignore
  }
  
  { new ISql with
      member this.FetchMany sql parameters mapper = fetchMany sql parameters mapper
      member this.FetchSingle sql parameters mapper = fetchSingle sql parameters mapper
      member this.TryFetchSingle sql parameters mapper = tryFetchSingle sql parameters mapper
      member this.ExecuteInt sql parameters = executeInt sql parameters
      member this.Execute sql parameters = execute sql parameters
  }     

let postgresParameterFactory name value =
  let toPostgresValue (postgresBaseType:NpgsqlDbType) parameterValue =
    match parameterValue with
    | SqlValueType.Optional v -> postgresBaseType, match v with | Some sv -> box sv | None -> box DBNull.Value
    | SqlValueType.Required v -> postgresBaseType, box v
    | SqlValueType.List items -> postgresBaseType ||| NpgsqlDbType.Array, box (items |> List.toArray :> System.Collections.IEnumerable)
    
  let postgresType, postgresValue =
    match value with
    | SqlCommandParameterValue.Uuid parameterValue -> parameterValue |> toPostgresValue NpgsqlDbType.Uuid
    | SqlCommandParameterValue.String parameterValue -> parameterValue |> toPostgresValue NpgsqlDbType.Text
    | SqlCommandParameterValue.DateTime parameterValue -> parameterValue |> toPostgresValue NpgsqlDbType.Timestamp
    | SqlCommandParameterValue.Integer parameterValue -> parameterValue |> toPostgresValue NpgsqlDbType.Integer
    | SqlCommandParameterValue.Long parameterValue -> parameterValue |> toPostgresValue NpgsqlDbType.Bigint
    | SqlCommandParameterValue.Float parameterValue -> parameterValue |> toPostgresValue NpgsqlDbType.Double
    | SqlCommandParameterValue.Boolean parameterValue -> parameterValue |> toPostgresValue NpgsqlDbType.Boolean
  NpgsqlParameter(name, postgresType, Value=postgresValue)

let postgresCommandFactory sql (connection:DbConnection) =
  (new NpgsqlCommand(sql, connection :?> NpgsqlConnection)) :> DbCommand
  
let sqlServerParameterFactory name value =
  let toSqlServerValue (postgresBaseType:SqlDbType) parameterValue =
    match parameterValue with
    | SqlValueType.Optional v -> postgresBaseType, match v with | Some sv -> box sv | None -> box DBNull.Value
    | SqlValueType.Required v -> postgresBaseType, box v
    | SqlValueType.List _ -> raise (NotImplementedException "List not yet supported on SQL Server")
    //| SqlValueType.List items -> postgresBaseType ||| SqlDbType. , box (items |> List.toArray :> System.Collections.IEnumerable)
    
  let sqlType, sqlValue =
    match value with
    | SqlCommandParameterValue.Uuid parameterValue -> parameterValue |> toSqlServerValue SqlDbType.UniqueIdentifier
    | SqlCommandParameterValue.String parameterValue -> parameterValue |> toSqlServerValue SqlDbType.NVarChar
    | SqlCommandParameterValue.DateTime parameterValue -> parameterValue |> toSqlServerValue SqlDbType.DateTime
    | SqlCommandParameterValue.Integer parameterValue -> parameterValue |> toSqlServerValue SqlDbType.Int
    | SqlCommandParameterValue.Long parameterValue -> parameterValue |> toSqlServerValue SqlDbType.BigInt
    | SqlCommandParameterValue.Float parameterValue -> parameterValue |> toSqlServerValue SqlDbType.Float
    | SqlCommandParameterValue.Boolean parameterValue -> parameterValue |> toSqlServerValue SqlDbType.Bit
  SqlParameter(name, sqlType, Value=sqlValue)
  
let sqlServerCommandFactory sql (connection:DbConnection) =
  (new SqlCommand(sql, connection :?> SqlConnection)) :> DbCommand
  
let postgres<'a> = sql postgresCommandFactory postgresParameterFactory
let sqlServer<'a> = sql sqlServerCommandFactory sqlServerParameterFactory

let createPostgresConnection connectionString = async {
  let connection = (new NpgsqlConnection(connectionString))
  do! connection.OpenAsync () |> Async.AwaitTask
  return connection
}

let createSqlServerConnection connectionString = async {
  let connection = (new SqlConnection(connectionString))
  do! connection.OpenAsync () |> Async.AwaitTask
  return connection
}