# Formulas

`payroll` is the table on the Data sheet that Power Query loads from the PDF. Year comparisons always use `payroll[PeriodType],"Year"` so the part year (Sep 2017 to Mar 2018) and the four months of 2025 are left out.

## Named ranges

| Name | Refers to | What it is |
|---|---|---|
| SelState, SelFY, SelAge | Dashboard!$B$7, $B$10, $B$13 | the three dropdowns |
| StateList | Lookups!$K$8# | `=SORT(UNIQUE(payroll[State]))` |
| YearList | Lookups!$M$8# | `=SORT(UNIQUE(FILTER(payroll[FY],payroll[PeriodType]="Year")))` |
| AgeChoices | Lookups!$I$8:$I$14 | "All ages" and the six age labels (17 and under ... 36 and over) |
| LatestFY, PeakFY, FirstFY | Lookups!$J$3:$J$5 | 2024-25, 2022-23, 2018-19 |
| AgeCrit | Calc!$B$1 | `=IF(SelAge="All ages","*",SelAge)`, used against payroll[AgeLabel], so SUMIFS matches every age when "All ages" is picked |
| PrevFY | Calc!$D$1 | `=IF(MATCH(SelFY,YearList,0)=1,"",INDEX(YearList,MATCH(SelFY,YearList,0)-1))` |
| SelValue | Calc!$F$1 | net payroll for the selected state, year and age group |

## Data sheet (calculated columns)

```
State     =XLOOKUP([@SourceName],StateMap[SourceName],StateMap[State],"Unmapped")
Region    =XLOOKUP([@SourceName],StateMap[SourceName],StateMap[Region],"Unmapped")
AgeOrder  =XLOOKUP([@Age],AgeMap[Age],AgeMap[Order])
Band      =XLOOKUP([@Age],AgeMap[Age],AgeMap[Band])
AgeLabel  =XLOOKUP([@Age],AgeMap[Age],AgeMap[Label])
```

## States sheet

```
A6  =SORTBY(StateList,SUMIFS(payroll[NetPayroll],payroll[State],StateList,payroll[FY],LatestFY,payroll[PeriodType],"Year"),-1)
B5  =TRANSPOSE(YearList)
B6  =SUMIFS(payroll[NetPayroll],payroll[State],A6#,payroll[FY],B5#,payroll[PeriodType],"Year")
J6  =SUMIFS(payroll[NetPayroll],payroll[State],A6#,payroll[FY],LatestFY,payroll[PeriodType],"Year")/SUMIFS(payroll[NetPayroll],payroll[FY],LatestFY,payroll[PeriodType],"Year")
K6  =SUMIFS(...,payroll[FY],LatestFY,...)/SUMIFS(...,payroll[FY],PeakFY,...)-1
L6  =SUMIFS(...,LatestFY,...,payroll[Band],"18-25")/SUMIFS(...,LatestFY,...)
M6  =IFERROR(SUMIFS(...,LatestFY,...)/SUMIFS(...,FirstFY,...),"n/a")
O2  =COUNTIF(K6#,"<0")&" of "&ROWS(A6#)&" states and UTs"
O6  =SORTBY(FILTER(A6#,K6#<0),FILTER(K6#,K6#<0),1)
P6  =XLOOKUP(O6#,A6#,K6#)
```

B6 gets the state list down the side and the year list across the top, so one SUMIFS fills the whole grid. Row 4 repeats the same calculations for all of India.

## Calc sheet (feeds the charts)

```
A4   =YearList
B4   =SUMIFS(payroll[NetPayroll],payroll[State],SelState,payroll[FY],A4#,payroll[PeriodType],"Year",payroll[AgeLabel],AgeCrit)
E4   =IFERROR(SUMIFS(...,SelState,...,SelFY,...,payroll[AgeLabel],D4:D9)/SUMIFS(...,SelState,...,SelFY,...),0)     age mix of the state
F4   =SUMIFS(...,SelFY,...,payroll[AgeLabel],D4:D9)/SUMIFS(...,SelFY,...)                                          age mix of India
H4   =INDEX(SORTBY(StateList,SUMIFS(...,payroll[State],StateList,payroll[FY],SelFY,...,payroll[AgeLabel],AgeCrit),-1),SEQUENCE(10))
I4   =SUMIFS(payroll[NetPayroll],payroll[State],H4#,payroll[FY],SelFY,payroll[PeriodType],"Year",payroll[AgeLabel],AgeCrit)
H17  =SORTBY(StateList,SUMIFS(...SelFY...AgeCrit),-1)                                                       full ranking
K4   =YearList,  L4:Q4  =SUMIFS(payroll[NetPayroll],payroll[FY],$K$4#,payroll[PeriodType],"Year",payroll[AgeLabel],L$3)
S4   =INDEX(States!A6#,SEQUENCE(15)),  T4 =INDEX(States!K6#,SEQUENCE(15))
```

## Dashboard

```
Net new payroll   =SelValue
Change            =IF(PrevFY="","n/a",IFERROR(SelValue/SUMIFS(...,SelState,...,PrevFY,...,AgeCrit)-1,"n/a"))
Share of India    =SelValue/SUMIFS(payroll[NetPayroll],payroll[FY],SelFY,payroll[PeriodType],"Year",payroll[AgeLabel],AgeCrit)
Rank              =MATCH(SelState,Calc!H17#,0)
Aged 18-25        =IFERROR(SUMIFS(...,SelState,...,SelFY,...,payroll[Band],"18-25")/SUMIFS(...,SelState,...,SelFY,...),"n/a")
Best year         =INDEX(Calc!A4#,MATCH(MAX(Calc!B4#),Calc!B4#,0))
```

## Checks

```
SumOfStates  =SUMIFS(payroll[NetPayroll],payroll[Period],[@Period],payroll[AgeLabel],[@Age])
Gap          =[@SumOfStates]-[@AllIndia]
Status       =IF([@Gap]=0,"OK",IF(ABS([@Gap])<=5,"Small gap","Check"))
Flagged      Value, Year before (INDEX/MATCH on YearList), Times year before
```
