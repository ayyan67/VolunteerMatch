from flask import Blueprint, render_template, session, request, send_file
import psycopg2
from io import BytesIO, StringIO
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

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
            SELECT u.username, e.event_name, e.event_date, vh.history_id
            FROM volunteer_history vh
            JOIN usercredentials u ON vh.user_id = u.id
            JOIN event_details e ON vh.event_id = e.event_id
            WHERE e.event_date BETWEEN %s AND %s
            ORDER BY e.event_date, u.username
        """, (start_date, end_date))
        data = cur.fetchall()
        headers = ['Volunteer Name', 'Event Name', 'Event Date', 'History ID']
    elif report_type == 'event_details':
        cur.execute("""
            SELECT e.event_name, e.event_date, e.location, e.required_skills, e.urgency, COUNT(vh.user_id) as volunteer_count
            FROM event_details e
            LEFT JOIN volunteer_history vh ON e.event_id = vh.event_id
            WHERE e.event_date BETWEEN %s AND %s
            GROUP BY e.event_id, e.event_name, e.event_date, e.location, e.required_skills, e.urgency
            ORDER BY e.event_date
        """, (start_date, end_date))
        data = cur.fetchall()
        headers = ['Event Name', 'Event Date', 'Location', 'Required Skills', 'Urgency', 'Volunteer Count']
    else:
        cur.close()
        return "Invalid report type", 400

    cur.close()

    report_name = f"{report_type}_{start_date}_to_{end_date}"

    if report_format == 'csv':
        return generate_csv(data, headers, report_name)
    elif report_format == 'pdf':
        return generate_pdf(data, headers, report_name)
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
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment

    elements.append(Paragraph(f"{report_name.replace('_', ' ').title()} Report", title_style))
    elements.append(Paragraph(f"", styles['Normal']))  # Add some space

    if 'event_details' in report_name:
        # Adjust column widths for event details
        col_widths = [1.5*inch, 1*inch, 1.5*inch, 3*inch, 0.8*inch, 1*inch]
        # Wrap the required skills text in Paragraphs to enable word wrap
        data = [[Paragraph(cell, styles['Normal']) if idx == 3 else cell for idx, cell in enumerate(row)] for row in data]
    else:
        col_widths = None  # Let ReportLab decide the column widths for volunteer participation

    table_data = [headers] + list(data)
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t)
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer,
                     mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"{report_name}.pdf")
