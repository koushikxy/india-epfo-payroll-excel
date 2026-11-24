section EPFO;

shared SourceFile = "data\epfo_payroll_september_2025.pdf" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true];

shared fnStatePage = (page as table) as table =>
let
    Cells = List.Combine(Table.ToRows(page)),
    AgeTitle = List.First(List.Select(Cells, each _ is text and Text.StartsWith(_, "Age Bucket:"))),
    Age = Text.Trim(Text.AfterDelimiter(AgeTitle, ":")),
    HeaderRow = List.PositionOf(page[Column1], "State"),
    Body = Table.Skip(page, HeaderRow),
    Promoted = Table.PromoteHeaders(Body, [PromoteAllScalars = true]),
    FirstPeriod = Table.ColumnNames(Promoted){1},
    RenameFirst = Table.RenameColumns(Promoted, {{FirstPeriod, "2017-18 (Sep-Mar)"}}),
    StateRows = Table.SelectRows(RenameFirst, each [State] <> null and [State] <> "" and not List.Contains({"SUB TOTAL", "Grand Total"}, Text.Trim([State]))),
    Unpivot = Table.UnpivotOtherColumns(StateRows, {"State"}, "Period", "NetPayroll"),
    AddAge = Table.AddColumn(Unpivot, "Age", each Age, type text)
in
    AddAge;

shared payroll_raw = let
    Source = Pdf.Tables(File.Contents(SourceFile), [Implementation = "1.3"]),
    Pages = Table.SelectRows(Source, each [Kind] = "Page"),
    StatePages = Table.SelectRows(Pages, each List.Contains([Data][Column1], "State")),
    ReadPage = Table.AddColumn(StatePages, "Rows", each fnStatePage([Data])),
    KeepCols = Table.SelectColumns(ReadPage, {"Id", "Rows"}),
    Expand = Table.ExpandTableColumn(KeepCols, "Rows", {"State", "Period", "NetPayroll", "Age"}),
    Renamed = Table.RenameColumns(Expand, {{"Id", "Page"}})
in
    Renamed;

shared payroll = let
    Source = payroll_raw,
    TrimText = Table.TransformColumns(Source, {{"State", each Text.Trim(Text.Clean(_)), type text}, {"Period", each Text.Trim(Text.Clean(_)), type text}}),
    PeriodType = Table.AddColumn(TrimText, "PeriodType", each
        if Text.StartsWith([Period], "2017-18") then "Part year"
        else if Text.Length([Period]) = 7 and Text.Middle([Period], 4, 1) = "-" then "Year"
        else "Month", type text),
    MonthDate = Table.AddColumn(PeriodType, "MonthDate", each
        if [PeriodType] = "Month" then Date.FromText("01-" & [Period], [Format = "dd-MMM-yy", Culture = "en-US"]) else null, type date),
    FY = Table.AddColumn(MonthDate, "FY", each
        if [PeriodType] = "Year" then [Period]
        else if [PeriodType] = "Part year" then "2017-18"
        else let y = Date.Year([MonthDate]) - (if Date.Month([MonthDate]) < 4 then 1 else 0) in Text.From(y) & "-" & Text.End(Text.From(y + 1), 2), type text),
    PeriodLabel = Table.TransformColumns(FY, {{"Period", each if Text.Length(_) = 6 and Text.Middle(_, 3, 1) = "-" then Text.Start(_, 3) & " 20" & Text.End(_, 2) else _, type text}}),
    Numbers = Table.TransformColumns(PeriodLabel, {{"NetPayroll", each Number.From(_), Int64.Type}}),
    Renamed = Table.RenameColumns(Numbers, {{"State", "SourceName"}}),
    Ordered = Table.SelectColumns(Renamed, {"FY", "Period", "PeriodType", "MonthDate", "SourceName", "Age", "NetPayroll", "Page"})
in
    Ordered;

shared india_totals = let
    Source = Pdf.Tables(File.Contents(SourceFile), [Implementation = "1.3"]),
    Page1 = Source{[Id = "Page001"]}[Data],
    HeaderRow = List.PositionOf(List.Transform(Page1[Column1], each if _ is text then Text.Start(_, 5) else null), "Month"),
    Body = Table.Skip(Page1, HeaderRow + 1),
    Picked = Table.SelectColumns(Body, {"Column1", "Column2", "Column3", "Column4", "Column5", "Column6", "Column7"}),
    Named = Table.RenameColumns(Picked, {{"Column1", "Period"}, {"Column2", "Less than 18"}, {"Column3", "18-21"}, {"Column4", "22-25"}, {"Column5", "26-28"}, {"Column6", "29-35"}, {"Column7", "More than 35"}}),
    CleanPeriod = Table.TransformColumns(Named, {{"Period", each if _ = null then null else Text.Trim(Text.Clean(_)), type text}}),
    DataRows = Table.SelectRows(CleanPeriod, each [Period] <> null and (Text.StartsWith([Period], "20") or List.Contains({"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"}, Text.Start([Period], 3)))),
    SameLabels = Table.TransformColumns(DataRows, {{"Period", each if Text.StartsWith(_, "2017-18") then "2017-18 (Sep-Mar)" else if Text.Length(_) = 8 and Text.Middle(_, 3, 1) = "-" then Text.Start(_, 3) & " " & Text.End(_, 4) else _, type text}}),
    Unpivot = Table.UnpivotOtherColumns(SameLabels, {"Period"}, "Age", "AllIndia"),
    AgeUnder = Table.ReplaceValue(Unpivot, "Less than 18", "17 and under", Replacer.ReplaceValue, {"Age"}),
    AgeOver = Table.ReplaceValue(AgeUnder, "More than 35", "36 and over", Replacer.ReplaceValue, {"Age"}),
    Types = Table.TransformColumnTypes(AgeOver, {{"AllIndia", Int64.Type}})
in
    Types;

