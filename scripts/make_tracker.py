"""Builds records/hilys-tracker.xlsx: families, lessons, payments, a monthly summary,
and the video-course sheets (waiting list and subscribers, pilot feedback, course summary).

    python scripts/make_tracker.py new-tracker.xlsx            builds a blank tracker
    python scripts/make_tracker.py --add-to your-tracker.xlsx  adds only the video-course sheets
                                                               to a tracker you already use

--add-to leaves your existing sheets and rows alone, and skips any sheet that is already there.
"""
import sys
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

add_to = sys.argv[1] == "--add-to"
out = sys.argv[2] if add_to else sys.argv[1]
ROWS = 500
NAVY, ORANGE, GREY = "1F2F86", "E8642C", "8A8FA8"
head_font = Font(bold=True, color="FFFFFF")
head_fill = PatternFill("solid", fgColor=NAVY)
example_font = Font(italic=True, color=GREY)

wb = load_workbook(out) if add_to else Workbook()

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

def core_sheets():
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


def course_sheets():
    """Video course: who is waiting or subscribed, what the pilot families said, and the totals."""
    made = []

    if "Video course" not in wb.sheetnames:
        vc = wb.create_sheet("Video course")
        sheet(vc,
              ["Parent", "Child(ren)", "Parent WhatsApp", "Country", "Date added", "Interested in",
               "Status", "Monthly USD", "Subscription start", "Heard about it from", "Notes"],
              [16, 18, 18, 12, 12, 14, 14, 11, 14, 16, 30],
              ["Example: Nomsa", "Example: Thandi", "+44 7700 900123", "UK", "2026-11-20", "HILYS Plus",
               "Waiting list", "", "", "WhatsApp", "Delete this example row"])
        dropdown(vc, "F", ["Self-paced", "HILYS Plus", "Not sure"])
        dropdown(vc, "G", ["Waiting list", "Pilot family", "Subscribed", "Stopped", "Not interested"])
        dropdown(vc, "J", ["WhatsApp", "Another family", "Website", "Live lessons", "Other"])
        for r in range(2, ROWS + 1):
            vc[f"H{r}"].number_format = '"$"#,##0.00'
        made.append("Video course")

    if "Pilot feedback" not in wb.sheetnames:
        fb = wb.create_sheet("Pilot feedback")
        sheet(fb,
              ["Date", "Parent", "Child", "Age", "How much they watched", "Child stayed interested (1-5)",
               "Sound and picture clear (1-5)", "Length", "Child joined in", "Best part", "Hardest part",
               "Would pay for the course", "Which way to learn", "Fair price per month USD",
               "Would tell another family", "Can we quote them?", "Notes"],
              [12, 16, 14, 6, 14, 14, 14, 12, 12, 26, 26, 12, 14, 12, 12, 12, 30],
              ["2026-12-01", "Example: Nomsa", "Example: Thandi", 7, "All of it", 4, 5, "About right", "Yes",
               "The clapping game", "The click sound", "Maybe", "HILYS Plus", 15, "Yes", "Yes",
               "Delete this example row"])
        dropdown(fb, "E", ["All of it", "Most of it", "About half", "Less than half"])
        dropdown(fb, "F", ["1", "2", "3", "4", "5"])
        dropdown(fb, "G", ["1", "2", "3", "4", "5"])
        dropdown(fb, "H", ["Too long", "About right", "Too short"])
        dropdown(fb, "I", ["Yes", "A little", "No"])
        dropdown(fb, "L", ["Yes", "Maybe", "No"])
        dropdown(fb, "M", ["Self-paced", "HILYS Plus", "Live lessons", "None"])
        dropdown(fb, "O", ["Yes", "Maybe", "No"])
        dropdown(fb, "P", ["Yes", "No"])
        for r in range(2, ROWS + 1):
            fb[f"N{r}"].number_format = '"$"#,##0'
        made.append("Pilot feedback")

    if "Course summary" not in wb.sheetnames:
        cs = wb.create_sheet("Course summary")
        sheet(cs, ["Video course", "Now", "Notes"], [34, 12, 60])
        rows = [
            ("Families on the waiting list", '=COUNTIF(\'Video course\'!G:G,"Waiting list")', ""),
            ("Pilot families", '=COUNTIF(\'Video course\'!G:G,"Pilot family")', "The plan is to show the Lesson 5 pilot to 5 families."),
            ("HILYS Plus subscribers", '=COUNTIFS(\'Video course\'!G:G,"Subscribed",\'Video course\'!F:F,"HILYS Plus")',
             "The plan's target before recruiting more teachers is 20."),
            ("Self-paced subscribers", '=COUNTIFS(\'Video course\'!G:G,"Subscribed",\'Video course\'!F:F,"Self-paced")', ""),
            ("Subscription income per month", '=SUMIFS(\'Video course\'!H:H,\'Video course\'!G:G,"Subscribed")',
             "Adds up Monthly USD for everyone marked Subscribed."),
            ("Families who stopped", '=COUNTIF(\'Video course\'!G:G,"Stopped")', ""),
            ("", "", ""),
            ("Pilot feedback forms", "=COUNTA('Pilot feedback'!A2:A%d)" % ROWS, "Counts the example row until you delete it."),
            ("Average: child stayed interested (1-5)", "=IFERROR(AVERAGE('Pilot feedback'!F2:F%d),\"\")" % ROWS, "4 or more is a good sign."),
            ("Average: sound and picture clear (1-5)", "=IFERROR(AVERAGE('Pilot feedback'!G2:G%d),\"\")" % ROWS, ""),
            ("Would pay: Yes", "=COUNTIF('Pilot feedback'!L:L,\"Yes\")", ""),
            ("Would pay: Maybe", "=COUNTIF('Pilot feedback'!L:L,\"Maybe\")", ""),
            ("Would pay: No", "=COUNTIF('Pilot feedback'!L:L,\"No\")", ""),
            ("Average fair price per month", "=IFERROR(AVERAGE('Pilot feedback'!N2:N%d),\"\")" % ROWS,
             "Compare with the prices on the website's courses page."),
        ]
        for label, formula, note in rows:
            cs.append([label, formula, note])
        for r in range(2, len(rows) + 2):
            cs[f"A{r}"].font = Font(bold=True)
            cs[f"C{r}"].font = Font(italic=True, color=GREY)
        for cell in ("B6", "B15"):
            cs[cell].number_format = '"$"#,##0.00'
        for cell in ("B10", "B11"):
            cs[cell].number_format = "0.0"
        made.append("Course summary")
    return made


if not add_to:
    core_sheets()
added = course_sheets()

wb.save(out)
print("saved", out, "| added:", ", ".join(added) if added else "nothing new (the course sheets were already there)")
