# report.py — PDF learning report using ReportLab
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from db import conn, SECTIONS

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

def make_report(start_day,end_day):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=34,leftMargin=34,topMargin=34,bottomMargin=34)
    styles=getSampleStyleSheet()
    title=styles["Title"]; body=styles["BodyText"]
    story=[Paragraph("Italian Coach - Learning Report",title),
           Paragraph(f"{start_day} to {end_day}",body),Spacer(1,12)]
    with conn() as c:
        prog=c.execute("""SELECT * FROM daily_progress WHERE day BETWEEN ? AND ?
                          ORDER BY day""",(start_day,end_day)).fetchall()
        acts=c.execute("""SELECT day,section,action,points,detail FROM activity_log
                          WHERE day BETWEEN ? AND ? ORDER BY day,id""",(start_day,end_day)).fetchall()
        learned=c.execute("""SELECT day,kind,display FROM learned_items
                             WHERE day BETWEEN ? AND ? ORDER BY day,id""",(start_day,end_day)).fetchall()
        scores=c.execute("""SELECT day,kind,ref,score FROM attempts
                            WHERE day BETWEEN ? AND ? ORDER BY day,id""",(start_day,end_day)).fetchall()
    data=[["Date"]+[s.title() for s in SECTIONS]]
    for r in prog:data.append([r["day"]]+["Yes" if r[s] else "-" for s in SECTIONS])
    if len(data)>1:
        story += [Paragraph("Daily completion",styles["Heading2"]),
                  Table(data,repeatRows=1,style=[("GRID",(0,0),(-1,-1),.4,colors.grey),
                  ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("FONTSIZE",(0,0),(-1,-1),7)]),Spacer(1,14)]
    story.append(Paragraph("Learned vocabulary and expressions",styles["Heading2"]))
    for r in learned:
        story.append(Paragraph(f'{r["day"]} - {r["kind"]}: {r["display"]}',body))
    story += [Spacer(1,12),Paragraph("Exercise scores",styles["Heading2"])]
    for r in scores:story.append(Paragraph(f'{r["day"]} - {r["kind"]} {r["ref"]}: {r["score"]}',body))
    story += [Spacer(1,12),Paragraph("Activity log",styles["Heading2"])]
    for r in acts:story.append(Paragraph(f'{r["day"]} - {r["section"]}: {r["action"]} ({r["points"]}) {r["detail"]}',body))
    doc.build(story);buf.seek(0);return buf.getvalue()
