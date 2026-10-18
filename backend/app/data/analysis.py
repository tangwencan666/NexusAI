from decimal import Decimal
from app.data.models import ChartSpec,DataResult


class DataFrameAnalysisService:
    def analyze(self,result:DataResult)->tuple[ChartSpec|None,list[str]]:
        if not result.rows:return None,["The query returned no rows; no numerical conclusion can be drawn."]
        numeric=[key for key,value in result.rows[0].items() if isinstance(value,(int,float,Decimal))]
        dimensions=[key for key in result.columns if key not in numeric]
        if numeric and dimensions:
            x="month" if "month" in dimensions else dimensions[0]
            series=[value for value in dimensions if value!=x][:1]
            chart=ChartSpec(type="line" if x=="month" else "bar",title=f"{numeric[0].replace('_',' ').title()} by {x.replace('_',' ').title()}",x=x,y=numeric[0],series=series)
        else:chart=None
        values=[float(row[numeric[0]]) for row in result.rows if row.get(numeric[0]) is not None] if numeric else []
        insights=[f"The result contains {result.row_count} rows based on the executed SQL."]
        if values:insights.append(f"Observed {numeric[0]} ranges from {min(values):,.2f} to {max(values):,.2f}; no values were invented outside the result set.")
        if result.truncated:insights.append("The result was truncated, so conclusions may not cover all rows.")
        return chart,insights
