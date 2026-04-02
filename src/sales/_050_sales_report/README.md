# 050 Sales Reports

This module handles defining, executing, and exporting sales reports.

## Features

- Create report definitions (type, parameters, scheduling info)
- List and filter reports
- Execute reports (returns structured JSON data)
- Export reports as CSV

## Usage Example

```python
# Create a report definition
from src.sales._050_sales_report.schemas import ReportDefinitionCreate
from src.sales._050_sales_report.models import ReportType

data = ReportDefinitionCreate(
    name="Monthly Revenue by Region",
    report_type=ReportType.by_region,
    parameters={"region": ""} # all regions
)
```
