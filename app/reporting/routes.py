from flask import Blueprint, render_template, session, request, send_file
import psycopg2
from datetime import datetime
from io import BytesIO, StringIO
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

reporting_bp = Blueprint('reporting', __name__)

# Connect to the database
conn = psycopg2.connect(database="volunteers_db", user="postgres",
                        password="arti", host="localhost", port="5432")


@reporting_bp.route('/', methods=['GET'])
def reporting():
    if session.get('signed_in') is None or session["signed_in"] == False:
        return render_template("index.html")

    if not session['is_admin']:
        return render_template('base.html', email=session['email'], username=session['username'],
                               is_admin=session['is_admin'])

    return render_template('generate_report.html', username=session['username'])


@reporting_bp.route('/generate_report', methods=['POST'])
def generate_report():
    if not session.get('is_admin'):
        return render_template("index.html")

    report_type = request.form.get('report_type')
    report_format = request.form.get('report_format')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    cur = conn.cursor()

    if report_type == 'volunteer_participation':
        cur.execute("""
            SELECT up.full_name, u.email, u.username, e.event_name, e.event_date
            FROM volunteer_history vh
            JOIN usercredentials u ON vh.user_id = u.id
            JOIN event_details e ON vh.event_id = e.event_id
            JOIN user_profile up ON up.user_id = u.id
            WHERE e.event_date BETWEEN %s AND %s
            ORDER BY e.event_date, u.username
        """, (start_date, end_date))
        data = cur.fetchall()
        data_csv, data_pdf = [], []

        headers = ['Name', 'Email', 'Events Assigned/Participated in']

        volunteers_dict = {}  # email -> [name, [event1, event2]]
        for name, email, username, event_name, event_date in data:
            if email in volunteers_dict:
                if event_name:
                    volunteers_dict[email][1].append(f"{event_name} ({event_date})")
            else:
                if event_name:
                    volunteers_dict[email] = [name, [f"{event_name} ({event_date})"]]
                else:
                    volunteers_dict[email] = [name, ["-"]]

        styles = getSampleStyleSheet()

        for email, val in volunteers_dict.items():
            name, events = val

            formatted_events_pdf = ""
            formatted_events_csv = "["
            for i, event in enumerate(events):
                formatted_events_pdf += event + ("<br /> <br />\n" if i < len(events) - 1 else "")
                formatted_events_csv += event + (", " if i < len(events) - 1 else "")
            formatted_events_csv += "]"

            data_pdf.append([Paragraph(name, styles["Normal"]), Paragraph(email, styles["Normal"]),
                             Paragraph(formatted_events_pdf, styles["Normal"])])
            data_csv.append([name, email, formatted_events_csv])

    elif report_type == 'event_details':
        cur.execute("""
            SELECT e.event_name, e.event_date, e.description, e.location, e.required_skills, e.urgency, up.full_name, uc.email, e.event_id
            FROM event_details e
            LEFT JOIN volunteer_history vh ON e.event_id = vh.event_id
            JOIN user_profile up ON up.user_id = vh.user_id
            JOIN usercredentials uc ON uc.id = vh.user_id
            WHERE e.event_date BETWEEN %s AND %s
            GROUP BY e.event_id, e.event_name, e.event_date, e.location, e.required_skills, e.urgency, up.full_name, uc.email
            ORDER BY e.event_date
        """, (start_date, end_date))
        data = cur.fetchall()
        data_csv, data_pdf = [], []

        headers = ['Event Name', 'Event Date', 'Description', 'Location', 'Required Skills', 'Urgency', 'Volunteers']

        styles = getSampleStyleSheet()

        event_dict = {}  # event_id -> [event_name, event_date, description, location,
        # required_skills, urgency, [volunteer1(email1), volunteer2(email2),...]]
        for details in data:
            event_name, event_date, description = details[0], details[1], details[2]
            location, required_skills, urgency = details[3], details[4], details[5]
            name, email, event_id = details[6], details[7], details[8]

            name_email = f"{name} ({email})"

            if event_id in event_dict:
                event_dict[event_id][-1].append(name_email)
            else:
                event_dict[event_id] = [event_name, event_date, description, location, required_skills,
                                        urgency, [name_email]]

        print(f"eventdict = {event_dict}")
        for event_id, event in event_dict.items():
            volunteers = event[-1]

            formatted_volunteers_pdf = ""
            formatted_volunteers_csv = "["
            for i, volunteer in enumerate(volunteers):
                formatted_volunteers_pdf += volunteer + ("<br /> <br />\n" if i < len(volunteers) - 1 else "")
                formatted_volunteers_csv += volunteer + (", " if i < len(volunteers) - 1 else "")

            formatted_volunteers_csv += "]"

            data_pdf.append([
                Paragraph(event_dict[event_id][0], styles["Normal"]),
                event_dict[event_id][1],
                Paragraph(event_dict[event_id][2], styles["Normal"]),
                Paragraph(event_dict[event_id][3], styles["Normal"]),
                Paragraph(event_dict[event_id][4], styles["Normal"]),
                Paragraph(event_dict[event_id][5], styles["Normal"]),
                Paragraph(formatted_volunteers_pdf, styles["Normal"])
            ])

            data_csv.append([
                event_dict[event_id][0],
                event_dict[event_id][1],
                event_dict[event_id][2],
                event_dict[event_id][3],
                event_dict[event_id][4],
                event_dict[event_id][5],
                formatted_volunteers_csv
            ])

    else:
        cur.close()
        return "Invalid report type", 400

    cur.close()

    report_name = f"{report_type}_{start_date}_to_{end_date}"

    if report_format == 'csv':
        return generate_csv(data_csv, headers, report_name)
    elif report_format == 'pdf':
        return generate_pdf(data_pdf, headers, report_name)
    else:
        return "Invalid report format", 400


def generate_csv(data, headers, report_name):
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(headers)
    cw.writerows(data)
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output,
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name=f"{report_name}.csv")


def generate_pdf(data, headers, report_name):
    buffer = BytesIO()
    doc = (SimpleDocTemplate(buffer, pagesize=landscape(letter)))
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment

    elements.append(Paragraph(f"{report_name.replace('_', ' ').title()} Report", title_style))
    elements.append(Paragraph(f"", styles['Normal']))  # Add some space

    subtitle = f"Report generated on {datetime.now()}."
    elements.append(Paragraph(subtitle, ParagraphStyle(
        name='CenteredHeading4',
        parent=styles['Heading4'],
        alignment=TA_CENTER
    )))

    if 'event_details' in report_name:
        # Adjust column widths for event detail
        col_widths = [1.5 * inch, 1 * inch, 1.5 * inch, 1.8 * inch, 1.8 * inch, 0.8 * inch, 2 * inch]
    else:
        col_widths = [2 * inch, 2.5 * inch, 4 * inch]

    table_data = [headers] + list(data)
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.append(t)
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer,
                     mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"{report_name}.pdf")
