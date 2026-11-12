"""Builds records/hilys-tracker.xlsx: families, lessons, payments and a monthly summary."""
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

out = sys.argv[1]
ROWS = 500
NAVY, ORANGE, GREY = "1F2F86", "E8642C", "8A8FA8"
head_font = Font(bold=True, color="FFFFFF")
head_fill = PatternFill("solid", fgColor=NAVY)
example_font = Font(italic=True, color=GREY)

wb = Workbook()

def sheet(ws, headers, widths, example=None):
    ws.append(headers)
    for c, w in zip(ws[1], widths):
        c.font, c.fill = head_font, head_fill
        c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    if example:
        ws.append(example)
        for c in ws[2]:
            c.font = example_font

def dropdown(ws, col, options):
    dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{col}2:{col}{ROWS}")

# Families
fam = wb.active
fam.title = "Families"
sheet(fam,
      ["Child", "Age", "Parent", "Parent WhatsApp", "Country", "Level", "Lesson type",
       "Lessons a week", "Group with", "Lesson day & UK time", "Start date", "Status", "Notes"],
      [16, 6, 16, 18, 12, 14, 13, 10, 18, 22, 12, 12, 30],
      ["Example: Thandi", 7, "Example: Nomsa", "+44 7700 900123", "UK", "Beginner", "One-to-one",
       2, "", "Tue & Thu 4:30pm", "2026-11-03", "Trial", "Delete this example row"])
dropdown(fam, "F", ["Beginner", "Intermediate", "Conversation"])
dropdown(fam, "G", ["One-to-one", "Group"])
dropdown(fam, "H", ["1", "2", "4"])
dropdown(fam, "L", ["Trial", "Active", "Paused", "Stopped"])

# Lessons
les = wb.create_sheet("Lessons")
sheet(les,
      ["Date", "UK time", "Child (or group)", "Lesson type", "Lesson / topic", "What happened",
       "Make-up owed?", "Make-up date", "Notes", "Month"],
      [12, 9, 20, 13, 24, 22, 12, 12, 30, 9],
      ["2026-11-03", "4:30pm", "Example: Thandi", "Trial", "Trial lesson", "Taught", "No", "",
       "Level: Beginner. Delete this example row", ""])
dropdown(les, "D", ["One-to-one", "Group", "Trial"])
dropdown(les, "F", ["Taught", "Moved (24h notice)", "Missed (counts as used)",
                    "Cancelled by HILYS", "Cut short (power/internet)"])
dropdown(les, "G", ["Yes", "No"])
for r in range(2, ROWS + 1):
    les[f"J{r}"] = f'=IF(A{r}="","",IF(ISNUMBER(A{r}),TEXT(A{r},"yyyy-mm"),LEFT(A{r},7)))'
    les[f"J{r}"].font = Font(color=GREY)
les.conditional_formatting.add(f"A2:I{ROWS}", FormulaRule(
    formula=[f'$G2="Yes"'], fill=PatternFill("solid", fgColor="FDE3D6")))

# Payments
pay = wb.create_sheet("Payments")
sheet(pay,
      ["Date received", "Parent", "Child(ren)", "Month paid for (yyyy-mm)", "Amount USD",
       "Method", "Reference", "Package", "Notes"],
      [13, 16, 18, 14, 11, 18, 18, 20, 30],
      ["2026-11-01", "Example: Nomsa", "Example: Thandi", "2026-11", 0, "Mukuru", "MK123456",
       "2 a week, one-to-one", "Delete this example row"])
dropdown(pay, "F", ["Mukuru", "EcoCash Diaspora", "Western Union", "Other"])
for r in range(2, ROWS + 1):
    pay[f"E{r}"].number_format = '"$"#,##0.00'

# Monthly summary
summ = wb.create_sheet("Monthly summary")
sheet(summ,
      ["Month", "Income USD", "Lessons taught", "Lessons missed", "Make-ups owed",
       "Active children", "Notes"],
      [10, 12, 12, 12, 12, 12, 40])
months = [f"{y}-{m:02d}" for y, m in
          [(2026, 11), (2026, 12)] + [(2027, k) for k in range(1, 11)]]
for i, mth in enumerate(months, start=2):
    summ[f"A{i}"] = mth
    summ[f"B{i}"] = f'=SUMIFS(Payments!E:E,Payments!D:D,A{i})'
    summ[f"C{i}"] = f'=COUNTIFS(Lessons!J:J,A{i},Lessons!F:F,"Taught")'
    summ[f"D{i}"] = f'=COUNTIFS(Lessons!J:J,A{i},Lessons!F:F,"Missed (counts as used)")'
    summ[f"E{i}"] = f'=COUNTIFS(Lessons!J:J,A{i},Lessons!G:G,"Yes")'
    summ[f"F{i}"] = '=COUNTIF(Families!L:L,"Active")' if i == 2 else ""
    summ[f"B{i}"].number_format = '"$"#,##0.00'
total = len(months) + 2
summ[f"A{total}"] = "Total"
summ[f"B{total}"] = f"=SUM(B2:B{total-1})"
summ[f"C{total}"] = f"=SUM(C2:C{total-1})"
summ[f"B{total}"].number_format = '"$"#,##0.00'
for c in summ[total]:
    c.font = Font(bold=True)
summ[f"G2"] = "Active children shows today's count. Register the business at about 10 paying children."
summ["G2"].font = Font(italic=True, color=GREY)

# Prices
pr = wb.create_sheet("Prices")
sheet(pr, ["Package", "One-to-one / month", "Group, per child / month"], [22, 18, 22])
for row in [["Per lesson", 12, 8], ["1 lesson a week", 48, 32],
            ["2 lessons a week", 96, 64], ["4 lessons a week", 192, 128]]:
    pr.append(row)
for r in range(2, 6):
    for col in "BC":
        pr[f"{col}{r}"].number_format = '"$"#,##0'
pr["A7"] = "A month counts as 4 lessons for each weekly slot. Change prices here and on the website together."
pr["A7"].font = Font(italic=True, color=GREY)

wb.save(out)
print("saved", out)
