import os
import csv
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from utils import get_today_date, format_datetime

EXPORTS_DIR = "exports"

def ensure_export_dir(date):
    """Создает папку для экспорта за указанную дату"""
    date_dir = os.path.join(EXPORTS_DIR, date)
    os.makedirs(date_dir, exist_ok=True)
    return date_dir

def export_to_csv(logs, date):
    date_dir = ensure_export_dir(date)
    filename = f"logs_{date}.csv"
    filepath = os.path.join(date_dir, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['ФИО', 'Действие', 'Локация', 'Комментарий', 'Время'])

        for log in logs:
            writer.writerow([
                log['full_name'],
                log['action'],
                log['location'],
                log['comment'] or "",
                format_datetime(log['timestamp'])
            ])

    return filepath

def export_to_excel(logs, date):
    date_dir = ensure_export_dir(date)
    filename = f"logs_{date}.xlsx"
    filepath = os.path.join(date_dir, filename)

    # Формируем данные
    data = []
    for log in logs:
        data.append({
            'ФИО': log['full_name'],
            'Действие': log['action'],
            'Локация': log['location'],
            'Комментарий': log['comment'] or "",
            'Время': format_datetime(log['timestamp'])
        })

    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)

    return filepath

def export_to_pdf(logs, date):
    date_dir = ensure_export_dir(date)
    filename = f"logs_{date}.pdf"
    filepath = os.path.join(date_dir, filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 10)

    # Заголовок
    pdf.cell(200, 10, txt=f"Журнал действий за {date}", ln=True, align='C')
    pdf.ln(5)

    # Заголовки столбцов
    col_widths = [40, 25, 40, 50, 35]
    headers = ['ФИО', 'Действие', 'Локация', 'Комментарий', 'Время']

    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, txt=header, border=1)
    pdf.ln()

    # Данные
    for log in logs:
        pdf.cell(col_widths[0], 10, txt=log['full_name'], border=1)
        pdf.cell(col_widths[1], 10, txt=log['action'], border=1)
        pdf.cell(col_widths[2], 10, txt=log['location'], border=1)
        pdf.cell(col_widths[3], 10, txt=log['comment'] or "", border=1)
        pdf.cell(col_widths[4], 10, txt=format_datetime(log['timestamp']), border=1)
        pdf.ln()

    pdf.output(filepath)
    return filepath