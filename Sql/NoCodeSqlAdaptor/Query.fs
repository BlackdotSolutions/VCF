module Query
open System
open Configuration
open FSharp.Control
open ApiTypes
open SqlAccess

type ScoredResult =
  { Id: string ; Title: string ; Score : float ; Source : string ; OutputEntity: OutputEntity option }

let private getOwnerAndTableName (searchEntity:SearchEntity) =
  let components = searchEntity.Name.Split "."
  match components with
  | [|tn|] -> None, tn
  | [|o ; tn|] -> (Some o),tn
  | _ -> raise (BadConfiguration "Table name must be in the format 'table' or 'schema.table'")

let private getSearchColumns sqlConnection (searchEntity:SearchEntity) = 
  match searchEntity.SearchColumns with
  | Some searchColumns -> async { return searchColumns }
  | None -> async {
    // we discover the columns we can search and give them all a weighting of 1
    let ownerOption, tableName = searchEntity |> getOwnerAndTableName
    let schemaSql = ownerOption |> Option.map(fun _ -> "AND TABLE_SCHEMA = @schema") |> Option.defaultValue ""
    let sql = $"""
      SELECT COLUMN_NAME as ColumnName
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_NAME = @tableName
      {schemaSql}
      AND CHARACTER_SET_NAME is not null
      ORDER BY ORDINAL_POSITION
    """
    let parameters = [
      "tableName", Parameter.Value tableName
      "schema", Parameter.Value (defaultArg ownerOption "")
    ]
    let resultMapper (row:RowReader) : SearchColumn = { Name = row.string "ColumnName" ; Weight = None }
    return! (sqlServer sqlConnection).FetchMany sql parameters resultMapper
  }

let private getKey sqlConnection (searchEntity:SearchEntity) = 
  match searchEntity.Key with
  | Some key -> async { return key }
  | None -> async {
    // TODO: this needs a bit of work to improve error handling around no primary key and compound primary key
    // (you can imagine making compound key work through concatentation but it would involve assumptions that may
    // not hold in a given database - probably better to ask users to use a view and specify a key in that scenario)
    let ownerOption, tableName = searchEntity |> getOwnerAndTableName
    let schemaSql = ownerOption |> Option.map(fun _ -> "AND TABLE_SCHEMA = @schema") |> Option.defaultValue ""
    let sql = $"""
      SELECT COLUMN_NAME as ColumnName
      FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
      WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + QUOTENAME(CONSTRAINT_NAME)), 'IsPrimaryKey') = 1
      AND TABLE_NAME = @tableName
      {schemaSql}
    """
    let parameters = [
      "tableName", Parameter.Value tableName
      "schema", Parameter.Value (defaultArg ownerOption "")
    ]
    let resultMapper (row:RowReader) = row.string "ColumnName"
    return! (sqlServer sqlConnection).FetchSingle sql parameters resultMapper
  }

let executeSqlServer connection maxResults (query:string) searchEntity = async {
  use! sqlConnection = createSqlServerConnection connection.ConnectionString
  let entityAttributeColumnName index = $"ecol{index}"
  let! searchColumns = getSearchColumns sqlConnection searchEntity
  let! searchEntityKey = getKey sqlConnection searchEntity
  let scoreCalculation =
    searchColumns
    |> List.map(fun searchColumn ->
      let weight = defaultArg searchColumn.Weight 1
      if (defaultArg searchEntity.ScoreBasedOnMatchCount true) then
        $"((LEN([{searchColumn.Name}])-LEN(REPLACE([{searchColumn.Name}],@query,'')))/LEN(@query)*{weight})"
      else
        $"(case when charindex(@query,[{searchColumn.Name}]) > 0 then {weight} else 0 end)"
    )
    |> (fun strings -> String.Join(" + ", strings))
  let entityColumnsSql =
    searchEntity.EntityDefinition
    |> Option.map(fun entityDefinition ->
      entityDefinition.EntityAttributes
      |> Seq.mapi(fun index mapping ->
        $", cast([{mapping.FromColumn}] as nvarchar) as {index |> entityAttributeColumnName}"
      )
      |> String.concat "\n"
    )
    |> Option.defaultValue ""
  let sqlText = $"""
select top {maxResults} * from (
  select CAST(({searchEntityKey}) as nvarchar) as Id,
         ({searchEntity.Title}) as Title,
         CAST(({scoreCalculation}) as float) as Score
         {entityColumnsSql}
    from {searchEntity.Name}) tbl
 where tbl.Score > 0
 order by tbl.Score desc
"""

  let parameters = [ "query", Parameter.Value query ]
  let resultMapper (row:RowReader) : ScoredResult =
    { Id = row.string "Id"
      Title = row.string "Title"
      Score = row.float "Score"
      Source = searchEntity.Source
      OutputEntity =
        searchEntity.EntityDefinition
        |> Option.map (fun entityDefinition ->
          { Type = entityDefinition.EntityType
            Id = System.Guid.NewGuid().ToString() //row.string "Id"
            Attributes =
              entityDefinition.EntityAttributes
              |> List.mapi(fun index mapping ->
                (mapping.ToAttribute, row.string (index |> entityAttributeColumnName))
                )
              |> Map.ofList
          }
        )
    }
  
  let! results = (sqlServer sqlConnection).FetchMany sqlText parameters resultMapper
  return results
}

let executeQuery connection maxResults query = async {
  let executer =
    match connection.ServerType with
    | DatabaseType.SQLServer -> executeSqlServer connection maxResults query
    | DatabaseType.SQLServerFullText -> raise (NotImplementedException "Full text not yet implemented")
    | DatabaseType.Postgres -> raise (NotImplementedException "Postgres not yet implemented")
    
  let! results =
    connection.Entities
    |> List.map(fun entity -> async {
      return! (executer entity)
    })
    |> Async.Sequential
    
  return
    results
    |> List.concat
    |> List.sortByDescending(fun src -> src.Score)
    |> List.truncate maxResults
    |> List.map(fun src ->
      { Key = src.Id
        Title = Some src.Title
        Subtitle = None
        Url = None
        Summary = None
        Source = Some src.Source
        Entities = src.OutputEntity |> Option.map(fun outputEntity -> [ outputEntity ])
      }
    )
    |> (fun output -> { SearchResults = output })
}

