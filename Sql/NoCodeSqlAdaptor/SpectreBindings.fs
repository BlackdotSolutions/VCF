module Spectre.Console.FSharp

open System
open Spectre.Console
open Spectre.Console.Rendering

type Color = Spectre.Console.Color
let render (renderable:IRenderable) = AnsiConsole.Write renderable

[<RequireQualifiedAccess>]
type FormatType =
  | String of string
  | Bool of bool
  | Int of int
  | UInt of uint
  | Long of int64
  | ULong of uint64
  | Float of float
  | Single of single
  | Decimal of decimal
  | Char of char
  | CharArray of char array
  with
    static member ($) (_, x:string) = FormatType.String x
    static member ($) (_, x:bool) = FormatType.Bool x
    static member ($) (_, x:int) = FormatType.Int x
    static member ($) (_, x:uint) = FormatType.UInt x
    static member ($) (_, x:int64) = FormatType.Long x
    static member ($) (_, x:uint64) = FormatType.ULong x
    static member ($) (_, x:float) = FormatType.Float x
    static member ($) (_, x:single) = FormatType.Single x
    static member ($) (_, x:decimal) = FormatType.Decimal x
    static member ($) (_, x:char) = FormatType.Char x
    static member ($) (_, x:char array) = FormatType.CharArray x
    
let inline (|FormatType|) x = Unchecked.defaultof<FormatType> $ x
  
let inline writeLineWithFormatProvider (formatProvider:IFormatProvider) value =
  match value with
  | FormatType.String v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.Bool v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.Int v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.UInt v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.Long v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.ULong v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.Float v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.Single v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.Decimal v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.Char v -> AnsiConsole.WriteLine (formatProvider,v)
  | FormatType.CharArray v -> AnsiConsole.WriteLine (formatProvider,v)

let inline writeLine (FormatType (value:FormatType)) = writeLineWithFormatProvider System.Globalization.CultureInfo.CurrentCulture value  


// Color shortcuts - help with readable styling
let Black = Color.Black
let Blue = Color.Blue
let Aqua = Color.Aqua
let Navy = Color.Navy
let Teal = Color.Teal
let Grey = Color.Grey
let Green = Color.Green
let Purple = Color.Purple
let Maroon = Color.Maroon
let Olive = Color.Olive
let Silver = Color.Silver
let Lime = Color.Lime
let Fuchsia = Color.Fuchsia
let Red = Color.Red
let White = Color.White
let Yellow = Color.Yellow

type TextStyle =
  | ForegroundColor of Color
  | BackgroundColor of Color
  | Bold
  | Dim
  | Italic
  | Underline
  | Invert
  | Conceal
  | SlowBlink
  | RapidBlink
  | Strikethrough
  | Link of string
  
type TextOverflow =
  | Fold
  | Crop
  | Ellipsis
  
let private setOverflow (overflowable:IOverflowable) textOverflow =
  overflowable.Overflow <-
    match textOverflow with
    | Fold -> Overflow.Fold
    | Crop -> Overflow.Crop
    | Ellipsis -> Overflow.Ellipsis
  
let private buildStyleString styles =    
  styles
  |> List.map (fun style ->
    match style with
    | ForegroundColor color -> color.ToString()
    | _ -> style.ToString().ToLower()
  )
  |> String.concat " "
  
let private buildStyleObject styles =
  styles
  |> List.fold (fun (newStyle:Style) styleProperty ->
    newStyle.Combine (
      match styleProperty with
      | ForegroundColor color -> Style(foreground=color)
      | BackgroundColor color -> Style(background=color)
      | Bold -> Style(decoration=(newStyle.Decoration ||| Decoration.Bold))
      | Dim -> Style(decoration=(newStyle.Decoration ||| Decoration.Dim))
      | Italic -> Style(decoration=(newStyle.Decoration ||| Decoration.Italic))
      | Underline -> Style(decoration=(newStyle.Decoration ||| Decoration.Underline))
      | Invert -> Style(decoration=(newStyle.Decoration ||| Decoration.Invert))
      | Conceal -> Style(decoration=(newStyle.Decoration ||| Decoration.Conceal))
      | SlowBlink -> Style(decoration=(newStyle.Decoration ||| Decoration.SlowBlink))
      | RapidBlink -> Style(decoration=(newStyle.Decoration ||| Decoration.RapidBlink))
      | Strikethrough -> Style(decoration=(newStyle.Decoration ||| Decoration.Strikethrough))
      | Link url -> Style(link=url)
    )
  ) Style.Plain

type HorizontalAlignment =
  | Left
  | Centered
  | Right
  
let private toJustify horizontalAlignment =
  match horizontalAlignment with
    | HorizontalAlignment.Left -> Justify.Left
    | HorizontalAlignment.Centered -> Justify.Center
    | HorizontalAlignment.Right -> Justify.Right
  
let private setAlignment (alignable:IAlignable) horizontalAlignment = alignable.Alignment <- horizontalAlignment |> toJustify    

type ContentType =
  | Text of string
  | Widget of IRenderable
  with
    member x.Renderable = match x with | Text t -> Spectre.Console.Text t :> IRenderable | Widget w -> w
    static member ($) (_, x:string) = Text(x)
    static member ($) (_, x:IRenderable) = Widget(x)

type TableColumnProp =
  | ColumnContentProp of ContentType
  | Alignment of HorizontalAlignment
  | Header of ContentType
  | Footer of ContentType
  | Width of int
  | NoWrap
  | PadLeft of int
  | PadRight of int
  | PadTop of int
  | PadBottom of int
  | Padding of int*int*int*int

type TableColumn =
  | ColumnProperties of TableColumnProp list
  | Text of string
  | Widget of IRenderable
  with
    static member ($) (_, x:TableColumnProp list) = ColumnProperties(x)
    static member ($) (_, x:string) = Text(x)
    static member ($) (_, x:IRenderable) = Widget(x)     
    
type TableProp =
  | Columns of TableColumnProp list list
  | Rows of ContentType list list
  | BorderStyle of TextStyle list

let inline (|ContentType|) x = Unchecked.defaultof<ContentType> $ x

let inline Content (ContentType (contentType:ContentType)) =
  match contentType with
  | ContentType.Text text -> ContentType.Text text
  | ContentType.Widget widget -> ContentType.Widget widget

let inline ColumnContent (ContentType (contentType:ContentType)) =
  match contentType with
  | ContentType.Text text -> ContentType.Text text |> ColumnContentProp
  | ContentType.Widget widget -> ContentType.Widget widget |> ColumnContentProp

let inline (|TableColumn|) x = Unchecked.defaultof<TableColumn> $ x

let inline Column (TableColumn (columnType:TableColumn)) =
  match columnType with
  | TableColumn.ColumnProperties properties -> properties
  | TableColumn.Text text -> [ TableColumnProp.ColumnContentProp (ContentType.Text text) ]
  | TableColumn.Widget widget -> [ TableColumnProp.ColumnContentProp (ContentType.Widget widget) ]
  
let inline Cell (ContentType (cellType:ContentType)) =
  cellType
  
type BarChartProp =
  | Bar of string*float*Color
  | Label of string
  | LabelAlignment of HorizontalAlignment
  | Width of int
  
type RuleProp =
  | Title of string
  | TitleAlignment of HorizontalAlignment
  | RuleStyle of TextStyle list
  | RuleStyleString of string
  
type TextProp =
  | Text of string
  | TextStyle of TextStyle list
  | TextAlignment of HorizontalAlignment
  | Overflow of TextOverflow
  
type PromptProp<'promptType> =
  | Message of string
  | InvalidChoiceMessage of string
  | Choices of 'promptType list
  | Validate of ('promptType -> Result<unit,string>)
  | PromptStyle of TextStyle list
  | IsSecret
  | ValidationErrorMessage of string
  | HideChoices
  | HideDefaultValue
  | DefaultValue of 'promptType
  | AllowEmpty
  | Converter of ('promptType -> string)
  
type SelectionPromptMode =
  | Leaf
  | Independent
  
type SelectionPromptProp<'promptType> =
  | Title of string
  | PageSize of int
  | MoreChoicesText of string
  | Choices of 'promptType list
  | HighlightStyle of TextStyle list
  | DisabledStyle of TextStyle list
  | Converter of ('promptType -> string)
  | SelectionMode of SelectionPromptMode
  
type CanvasProp =
  | Size of int*int
  | Fill of Color
  | Coxel of int*int*Color
  | Coxels of Color list list
  
module Widget =
  let Canvas properties =
    let defaultWidth,defaultHeight = 32,32
    // we use the coxels list of lists, if not defined we use the size if defined, and if not that the defaults 32x32
    let width,height =
      properties
      |> List.tryFind(function | Coxels _ -> true | _ -> false)
      |> (function | Some (Coxels coxels) ->
                     (defaultArg (coxels |> List.tryHead |> Option.map(fun a -> a.Length)) defaultWidth,
                      coxels.Length)
                   | _ ->
                     properties
                     |> List.tryFind(function | Size _ -> true | _ -> false)
                     |> (function | Some (Size (w,h)) -> w,h                    
                                  | _ -> (defaultWidth,defaultHeight)

                        )
         )
    let canvasRenderable = Canvas(width,height)
    properties
    |> List.iter (fun prop ->
      match prop with
      | Coxel (x,y,color) -> canvasRenderable.SetPixel(x,y,color) |> ignore
      | Coxels coxels ->
        coxels
        |> List.iteri (fun y row ->
          row
          |> List.iteri (fun x color ->
            canvasRenderable.SetPixel(x, y, color) |> ignore
          )
        )
      | Fill color ->
        {0..(canvasRenderable.Width-1)}
        |> Seq.iter (fun x ->
          {0..(canvasRenderable.Height-1)} |> Seq.iter (fun y -> canvasRenderable.SetPixel(x,y,color) |> ignore)
        )
      | _ -> ()
    )
    canvasRenderable
                     
  
  let Table properties =
    let tableRenderable = Table ()
    properties
    |> List.iter (fun prop ->
      match prop with
      | BorderStyle styles -> tableRenderable.BorderStyle <- styles |> buildStyleObject
      | Columns columns ->
        columns
        |> List.iter (fun columnProperties ->
          let newColumn =
            columnProperties
            |> List.tryFind (function | TableColumnProp.ColumnContentProp _ -> true | _ -> false)
            |> (function | Some (TableColumnProp.ColumnContentProp (ContentType.Text txt)) -> TableColumn(txt)
                         | Some (TableColumnProp.ColumnContentProp (ContentType.Widget widget)) -> TableColumn(widget)
                         | _ -> TableColumn("")
               )            
          columnProperties
          |> Seq.iter (fun columnProp ->
            match columnProp with
            | TableColumnProp.ColumnContentProp _ -> ()
            | Alignment alignment -> alignment |> setAlignment newColumn            
            | PadLeft v -> newColumn.PadLeft v |> ignore
            | PadRight v -> newColumn.PadRight v |> ignore
            | PadBottom v -> newColumn.PadBottom v |> ignore
            | PadTop v -> newColumn.PadTop v |> ignore
            | NoWrap -> newColumn.NoWrap <- true
            | TableColumnProp.Width w -> newColumn.Width <- w
            | Padding (left,top,right,bottom) -> newColumn.Padding <- Spectre.Console.Padding(left, top, right, bottom) 
            | Footer f -> newColumn.Footer <- f.Renderable
            | Header h -> newColumn.Header <- h.Renderable              
          )
          tableRenderable.AddColumn newColumn |> ignore
        )          
      | Rows rows -> rows |> List.iter(fun row -> tableRenderable.AddRow (row |> List.map(fun r -> r.Renderable) |> List.toArray) |> ignore)
    )
    tableRenderable
    
  let BarChart properties =
    let barChartRenderable = BarChart ()
    properties
    |> List.iter(fun prop ->
      match prop with
      | Bar (label,value,color) -> barChartRenderable.AddItem(label, value, color) |> ignore
      | BarChartProp.Label label -> barChartRenderable.Label <- label
      | BarChartProp.LabelAlignment alignment -> barChartRenderable.LabelAlignment <- alignment |> toJustify
      | Width width -> barChartRenderable.Width <- width
    )
    barChartRenderable :> IRenderable
    
  let Rule properties =
    let ruleRenderable = Rule()
    properties
    |> List.iter(fun prop ->
      match prop with
      | RuleProp.Title title -> ruleRenderable.Title <- title
      | RuleProp.TitleAlignment alignment -> alignment |> setAlignment ruleRenderable
      | RuleProp.RuleStyle styles -> ruleRenderable.Style <- styles |> buildStyleObject 
      | RuleProp.RuleStyleString styleString -> ruleRenderable.Style <- Style.Parse(styleString.Trim())
    )
    ruleRenderable :> IRenderable
    
  let Text properties =
    let textOrDefault =
      properties
      |> List.tryFind (function | TextProp.Text _ -> true | _ -> false)
      |> (function | Some (TextProp.Text txt) -> txt | _ -> "")
    let textRenderable =
      properties
      |> List.tryFind (function | TextProp.TextStyle _ -> true | _ -> false)
      |> (function | Some (TextProp.TextStyle textStyle) -> Spectre.Console.Text(textOrDefault, textStyle |> buildStyleObject)
                   | _ -> Spectre.Console.Text(textOrDefault)
         )
    properties
    |> List.iter(fun prop ->
      match prop with
      | TextStyle _
      | TextProp.Text _ -> ()
      | TextAlignment alignment -> alignment |> setAlignment textRenderable
      | Overflow textOverflow -> textOverflow |> setOverflow textRenderable         
    )
    textRenderable
    
module Prompt =
  let Confirm message = AnsiConsole.Confirm message
  
  let Ask<'a> message = AnsiConsole.Ask<'a> message
  
  let Prompt<'a> (properties:PromptProp<'a> list) =
    let textOrDefault =
      properties
      |> List.tryFind (function | PromptProp.Message _ -> true | _ -> false)
      |> (function | Some (PromptProp.Message txt) -> txt | _ -> "")
    
    let textPrompt = TextPrompt<'a>(textOrDefault)
    
    let wrapValidator validationFunction =
      System.Func<'a,ValidationResult> (
        fun state ->
          match validationFunction state with
          | Ok _ -> ValidationResult.Success()
          | Error msg -> ValidationResult.Error msg
      )
      
    properties
    |> List.iter(fun property ->
      match property with
      | Message _ -> ()
      | InvalidChoiceMessage message -> textPrompt.InvalidChoiceMessage <- message
      | PromptProp.Choices choices -> textPrompt.AddChoices choices |> ignore
      | Validate validationFunction -> textPrompt.Validator <- validationFunction |> wrapValidator
      | PromptStyle styles -> textPrompt.PromptStyle <- styles |> buildStyleObject
      | IsSecret -> textPrompt.IsSecret <- true
      | ValidationErrorMessage errorMessage -> textPrompt.ValidationErrorMessage <- errorMessage
      | HideChoices -> textPrompt.ShowChoices <- false
      | HideDefaultValue -> textPrompt.ShowDefaultValue <- false
      | AllowEmpty -> textPrompt.AllowEmpty <- true
      | PromptProp.Converter converterFunction -> textPrompt.Converter <- System.Func<'a,string> converterFunction
      | DefaultValue defaultValue -> textPrompt.DefaultValue defaultValue |> ignore
    )
    
    AnsiConsole.Prompt textPrompt
    
  let SelectionPrompt<'a> (properties:SelectionPromptProp<'a> list) =
    let selectionPrompt = SelectionPrompt<'a>()
    properties
    |> List.iter(fun property ->
      match property with
      | Title title -> selectionPrompt.Title <- title
      | PageSize pageSize -> selectionPrompt.PageSize <- pageSize
      | MoreChoicesText moreChoicesText -> selectionPrompt.MoreChoicesText <- moreChoicesText
      | Choices choices -> selectionPrompt.AddChoices(choices) |> ignore
      | HighlightStyle style -> selectionPrompt.HighlightStyle <- style |> buildStyleObject
      | DisabledStyle disabledStyle -> selectionPrompt.DisabledStyle <- disabledStyle |> buildStyleObject
      | Converter converterFunction -> selectionPrompt.Converter <- System.Func<'a,string> converterFunction
      | SelectionMode mode ->
        selectionPrompt.Mode <- match mode with | Leaf -> SelectionMode.Leaf | Independent -> SelectionMode.Independent
    )
    
    AnsiConsole.Prompt selectionPrompt
  
  
  
  

