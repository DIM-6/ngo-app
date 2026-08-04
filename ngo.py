import base64
from datetime import date, datetime, timedelta
import io
import os
import sqlite3
import urllib.parse
import pandas as pd
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

from reportlab.lib.pagesizes import A4, A6
from reportlab.pdfgen import canvas

# ==========================================
# DATABASE SETUP (SQLite)
# ==========================================
conn = sqlite3.connect("ngo_master.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name TEXT,
    phone TEXT,
    service_for_name TEXT,
    booking_date TEXT,
    meal_types TEXT,
    meal_prep_type TEXT,
    amount REAL,
    payment_status TEXT,
    payment_type TEXT,
    utr_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name TEXT,
    phone TEXT,
    donation_type TEXT,
    amount REAL,
    payment_mode TEXT,
    utr_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date TEXT,
    category TEXT,
    description TEXT,
    amount REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT,
    trans_type TEXT,
    quantity REAL,
    unit TEXT,
    entry_date TEXT,
    remarks TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS letters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outward_no TEXT,
    ref_no TEXT,
    letter_date TEXT,
    recipient TEXT,
    subject TEXT,
    body_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ==========================================
# NGO CONFIGURATION & RELATIVE PATHS
# ==========================================
NGO_NAME = "નર્મદેશ્વર વિકલાંગ વિકાસ માનવ સેવા ટ્રસ્ટ"
NGO_REG_NO = "F/5155/Mehsana (એફ/૫૧૫૫/મહેસાણા)"
NGO_PHONE = "917377174779"

LOGO_PATH = "rg_ngo_logo.png"
if not os.path.exists(LOGO_PATH):
    possible_paths = [
        "/home/dharmesh/NGO Work/rg_ngo_logo.png",
        "/home/dharmesh/NGO Work/rg_ngo_logo.jpg",
        "/home/dharmesh/NGO Work/rg_ngo_logo.jpeg",
        "rg_ngo_logo.jpg",
        "rg_ngo_logo.jpeg",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            LOGO_PATH = p
            break

BASE_DIR = os.getcwd()
RECEIPTS_DIR = os.path.join(BASE_DIR, "Receipts")
LETTERS_DIR = os.path.join(BASE_DIR, "Letters")
try:
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    os.makedirs(LETTERS_DIR, exist_ok=True)
except Exception:
    RECEIPTS_DIR = "/tmp/Receipts"
    LETTERS_DIR = "/tmp/Letters"
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    os.makedirs(LETTERS_DIR, exist_ok=True)


def get_image_base64(image_path):
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return ""
    return ""


def fmt_date(d_str):
    try:
        return datetime.strptime(str(d_str), "%Y-%m-%d").strftime("%d-%m-%Y")
    except Exception:
        return str(d_str)


MEAL_RATES = {
    "૧. સવારનો ચા-નાસ્તો": 500.0,
    "૨. બપોરનું ભોજન": 2000.0,
    "૩. સાંજનો નાસ્તો": 350.0,
    "૪. રાત્રિનું ભોજન": 1150.0,
}

ALL_MEALS = list(MEAL_RATES.keys())

st.set_page_config(
    page_title="NARMADESHWAR VIKLANG VIKAAS MANAV SEVA TRUST",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 🎨 CLEAN CSS WITH BALANCED LEFT-ALIGNED HEADER
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;600;700;800;900&display=swap');

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }

    label, p, span, div, h1, h2, h3, h4, .stMarkdown {
        font-family: 'Noto Sans Gujarati', sans-serif !important;
        color: #111827 !important;
    }

    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        color: #111827 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }

    input[type="text"], input[type="password"], input[type="number"] {
        text-transform: uppercase !important;
        background-color: #F9FAFB !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 6px !important;
    }

    /* Hide sidebar and unwanted icon text artifacts */
    [data-testid="stSidebar"] { display: none !important; }
    footer, #MainMenu { display: none !important; }

    /* ===== CARD BUTTON STYLING FOR JAMANVAR ===== */
    div.stButton > button {
        width: 100% !important;
        height: 95px !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 13.5px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 10px !important;
        white-space: pre-wrap !important;
    }

    /* ===== MAIN FORM SIZING FIXED ===== */
    .main .block-container {
        max-width: 900px !important;
        margin: 0 auto !important;
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
    }
    
    /* ===== HEADER STYLES (75% WIDTH, TIGHTLY GROUPED & LEFT ALIGNED) ===== */
    .header-wrapper {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 25px;
        margin-bottom: 5px;
        border-top: 5px solid #F39C12;
        padding-top: 15px;
        width: 75% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    .header-wrapper img {
        height: 120px !important; 
        width: auto; 
        object-fit: contain;
        flex-shrink: 0;
    }
    .header-text-box {
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: left;
        line-height: 1.35;
    }
    .h-title-1 { color: #16A34A !important; font-size: 24px !important; font-weight: 900 !important; margin: 0 !important; letter-spacing: 5px !important; }
    .h-title-2 { color: #0284C7 !important; font-size: 18px !important; font-weight: 800 !important; margin: 0 !important; letter-spacing: 4px !important; }
    .h-title-3 { color: #1E3A8A !important; font-size: 18px !important; font-weight: 800 !important; margin: 0 !important; letter-spacing: 4px !important; }
    .h-reg { color: #4B5563 !important; font-size: 11px !important; font-weight: bold !important; margin: 5px 0 0 0 !important; letter-spacing: 1.5px !important; }
    .h-sub-text { 
        color: #4B5563 !important; 
        font-size: 13px; 
        font-weight: bold; 
        margin-top: 6px; 
        display: flex; 
        gap: 8px; 
        flex-wrap: wrap; 
        justify-content: flex-start;
        letter-spacing: 1px !important;
    }

    @media (max-width: 768px) {
        .main .block-container {
            max-width: 100% !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        .header-wrapper {
            width: 100% !important;
            flex-direction: column !important;
            align-items: center !important;
            text-align: center !important;
            gap: 12px !important;
        }
        .header-text-box {
            text-align: center !important;
            align-items: center !important;
        }
        .h-sub-text {
            justify-content: center !important;
        }
        .header-wrapper img {
            height: 100px !important;
        }
        .h-title-1 { font-size: 20px !important; letter-spacing: 2px !important; }
        .h-title-2, .h-title-3 { font-size: 15px !important; letter-spacing: 2px !important; }
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 📄 AUTO-SAVE BACKEND PDF FUNCTION (RECEIPT)
# ==========================================
def auto_save_pdf_to_folder(booking_info):
    try:
        clean_donor_name = (
            "".join(
                c
                for c in booking_info["donor_name"]
                if c.isalnum() or c in (" ", "_", "-")
            )
            .strip()
            .replace(" ", "_")
        )

        filename = f"Receipt_No_{booking_info.get('id', 'N/A')}_{clean_donor_name}.pdf"
        file_path = os.path.join(RECEIPTS_DIR, filename)

        c = canvas.Canvas(file_path, pagesize=A6)
        width, height = A6

        c.setStrokeColorRGB(0.12, 0.23, 0.54)
        c.setLineWidth(1.5)
        c.rect(5, 5, width - 10, height - 10)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.08, 0.64, 0.29)
        c.drawString(70, height - 22, "NARMADESHWAR")

        c.setFillColorRGB(0.01, 0.52, 0.78)
        c.drawString(70, height - 33, "VIKLANG VIKAAS")

        c.setFillColorRGB(0.12, 0.23, 0.54)
        c.drawString(70, height - 44, "MANAV SEVA TRUST")

        c.setFont("Helvetica", 6.5)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawString(70, height - 53, "Reg. No: F/5155/Mehsana")

        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(
            10, height - 66, f"Receipt No: #{booking_info.get('id', 'N/A')}"
        )
        c.drawString(
            width - 80,
            height - 66,
            f"Date: {datetime.now().strftime('%d-%m-%Y')}",
        )

        c.line(10, height - 70, width - 10, height - 70)

        y = height - 85
        line_height = 13

        details = [
            ("Donor:", str(booking_info["donor_name"]).upper()),
            ("Phone:", str(booking_info["phone"])),
            ("Service For:", str(booking_info["service_for_name"]).upper()),
            ("Meal Date:", fmt_date(booking_info["booking_date"])),
            ("Meals:", str(booking_info["meal_types"])),
            ("Prep:", str(booking_info["meal_prep_type"])),
            ("Amount:", f"Rs. {booking_info['amount']:,.2f}"),
            (
                "Mode:",
                f"{booking_info['payment_type']} ({booking_info['payment_status']})",
            ),
        ]

        for label, val in details:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(12, y, label)
            c.setFont("Helvetica", 8)
            c.drawString(75, y, val[:25])
            y -= line_height

        c.setFont("Helvetica-Oblique", 7)
        c.setFillColorRGB(0.02, 0.59, 0.41)
        c.drawCentredString(
            width / 2, 12, "Thank you for your noble support!"
        )

        c.save()
        return file_path
    except Exception as e:
        return None


# ==========================================
# 🎯 COMPACT PRINTABLE HTML RECEIPT
# ==========================================
def render_html_receipt(booking_info):
    logo_b64 = get_image_base64(LOGO_PATH)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" class="receipt-logo" />'
        if logo_b64
        else ""
    )

    clean_donor = (
        "".join(
            c
            for c in booking_info["donor_name"]
            if c.isalnum() or c in (" ", "_", "-")
        )
        .strip()
        .replace(" ", "_")
        .upper()
    )
    pdf_file_name = f"Receipt_No_{booking_info.get('id', 'N/A')}_{clean_donor}"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{pdf_file_name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;600;700;800;900&display=swap');
            * {{ box-sizing: border-box; }}
            body {{
                font-family: 'Noto Sans Gujarati', Arial, sans-serif;
                background-color: #ffffff;
                margin: 0;
                padding: 4px;
                display: flex;
                justify-content: center;
            }}
            .receipt-box {{
                width: 100%;
                max-width: 380px;
                background: #ffffff;
                border: 1.5px solid #1e3a8a;
                border-radius: 8px;
                padding: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .header-flex {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                border-bottom: 1.5px solid #1e3a8a;
                padding-bottom: 6px;
                margin-bottom: 8px;
            }}
            .receipt-logo {{ height: 60px; width: auto; }}
            .title-box {{
                text-align: left;
                display: flex;
                flex-direction: column;
                justify-content: center;
                line-height: 1.1;
            }}
            .title-l1 {{ color: #16A34A; font-size: 14px; font-weight: 900; }}
            .title-l2 {{ color: #0284C7; font-size: 12px; font-weight: 800; }}
            .title-l3 {{ color: #1E3A8A; font-size: 12px; font-weight: 800; }}
            .reg-no {{ color: #4b5563; font-size: 9px; font-weight: 700; margin-top: 2px; }}
            .receipt-nametag {{ color: #1d4ed8; margin-top: 1px; font-size: 11px; font-weight: 700; }}
            .row {{
                display: flex;
                justify-content: space-between;
                padding: 4px 6px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 11px;
                gap: 6px;
            }}
            .row:nth-child(even) {{ background-color: #f8fafc; }}
            .label {{ font-weight: 600; color: #1e3a8a; flex-shrink: 0; }}
            .value {{ color: #111827; text-align: right; font-weight: 500; text-transform: uppercase; }}
            .total-row {{
                background-color: #eff6ff !important;
                font-weight: 700;
                color: #1e3a8a;
                font-size: 12px;
                border-top: 1px solid #1e3a8a;
                border-bottom: 1px solid #1e3a8a;
            }}
            .footer {{ text-align: center; margin-top: 8px; color: #059669; font-weight: 600; font-size: 10px; line-height: 1.3; }}
            .print-button {{
                display: block;
                width: 100%;
                background-color: #1e3a8a;
                color: white;
                text-align: center;
                padding: 8px;
                margin-top: 10px;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
                cursor: pointer;
            }}
            @media print {{
                @page {{ size: A6 portrait; margin: 0; }}
                .print-button {{ display: none; }}
                body {{ background-color: #ffffff; padding: 0; margin: 0; }}
                .receipt-box {{ border: 1px solid #000; box-shadow: none; width: 100%; border-radius: 0; }}
            }}
        </style>
        <script>
            function printReceipt() {{
                try {{ window.parent.document.title = "{pdf_file_name}"; }} catch(e) {{}}
                document.title = "{pdf_file_name}";
                window.print();
            }}
        </script>
    </head>
    <body>
        <div class="receipt-box">
            <div class="header-flex">
                <div class="logo-box">{logo_html}</div>
                <div class="title-box">
                    <div class="title-l1">NARMADESHWAR</div>
                    <div class="title-l2">VIKLANG VIKAAS</div>
                    <div class="title-l3">MANAV SEVA TRUST</div>
                    <div class="reg-no">Reg. No: {NGO_REG_NO}</div>
                    <div class="receipt-nametag">Receipt No: #{booking_info.get('id', 'N/A')}</div>
                </div>
            </div>
            <div class="row"><span class="label">પાવતી નં / No:</span><span class="value">#{booking_info.get('id', 'N/A')}</span></div>
            <div class="row"><span class="label">તારીખ / Date:</span><span class="value">{datetime.now().strftime('%d-%m-%Y')}</span></div>
            <div class="row"><span class="label">દાતાશ્રી / Donor:</span><span class="value">{booking_info['donor_name']}</span></div>
            <div class="row"><span class="label">મોબાઈલ / Mobile:</span><span class="value">{booking_info['phone']}</span></div>
            <div class="row"><span class="label">સેવા નામ / Service For:</span><span class="value">{booking_info['service_for_name']}</span></div>
            <div class="row"><span class="label">જમણવાર તારીખ:</span><span class="value">{fmt_date(booking_info['booking_date'])}</span></div>
            <div class="row"><span class="label">જમણવાર / Meal:</span><span class="value">{booking_info['meal_types']}</span></div>
            <div class="row"><span class="label">પ્રકાર / Prep Type:</span><span class="value">{booking_info['meal_prep_type']}</span></div>
            <div class="row total-row"><span>રકમ / Amount:</span><span>₹ {booking_info['amount']:,.2f}</span></div>
            <div class="row"><span class="label">પેમેન્ટ / Payment:</span><span class="value">{booking_info['payment_type']} ({booking_info['payment_status']})</span></div>
            <div class="footer">Thank you for your noble support!<br>આપના માનવસેવા યોગદાન બદલ આભાર!</div>
            <button class="print-button" onclick="printReceipt()">🖨️ પાવતી પ્રિન્ટ કરો / PDF સેવ કરો</button>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=530, scrolling=True)


# ==========================================
# 📜 PRINTABLE HTML LETTER
# ==========================================
def render_html_letter(letter_info):
    logo_b64 = get_image_base64(LOGO_PATH)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" style="height: 75px; width: auto;" />'
        if logo_b64
        else ""
    )

    pdf_file_name = f"Letter_Out_{letter_info.get('outward_no', 'N/A')}"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{pdf_file_name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;600;700;800;900&display=swap');
            * {{ box-sizing: border-box; }}
            body {{
                font-family: 'Noto Sans Gujarati', Arial, sans-serif;
                background-color: #ffffff;
                margin: 0;
                padding: 10px;
                display: flex;
                justify-content: center;
            }}
            .letter-box {{
                width: 100%;
                max-width: 700px;
                background: #ffffff;
                border: 2px solid #1e3a8a;
                border-radius: 8px;
                padding: 25px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            }}
            .header-flex {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
                border-bottom: 3px solid #F39C12;
                padding-bottom: 12px;
                margin-bottom: 15px;
            }}
            .title-box {{
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                line-height: 1.15;
            }}
            .title-l1 {{ color: #16A34A; font-size: 20px; font-weight: 900; }}
            .title-l2 {{ color: #0284C7; font-size: 15px; font-weight: 800; }}
            .title-l3 {{ color: #1E3A8A; font-size: 15px; font-weight: 800; }}
            .reg-no {{ color: #4b5563; font-size: 11px; font-weight: bold; margin-top: 3px; }}
            
            .meta-row {{
                display: flex;
                justify-content: space-between;
                font-weight: bold;
                font-size: 13px;
                margin-bottom: 15px;
                color: #1e3a8a;
            }}
            .recipient-box {{
                font-size: 13.5px;
                font-weight: bold;
                margin-bottom: 15px;
                line-height: 1.4;
            }}
            .subject-box {{
                font-size: 14px;
                font-weight: bold;
                text-decoration: underline;
                color: #1E3A8A;
            }}
            .ref-box {{
                font-size: 13px;
                font-weight: bold;
                color: #1e3a8a;
                margin-top: 8px;
                margin-bottom: 20px;
            }}
            .body-content {{
                font-size: 13.5px;
                line-height: 1.7;
                white-space: pre-wrap;
                margin-bottom: 30px;
                color: #111827;
            }}
            .signature-box {{
                float: right;
                text-align: center;
                font-weight: bold;
                font-size: 13.5px;
                margin-top: 20px;
            }}
            .print-button {{
                display: block;
                width: 100%;
                background-color: #1e3a8a;
                color: white;
                text-align: center;
                padding: 10px;
                margin-top: 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
            }}
            @media print {{
                @page {{ size: A4 portrait; margin: 15mm; }}
                .print-button {{ display: none; }}
                body {{ background-color: #ffffff; padding: 0; margin: 0; }}
                .letter-box {{ border: none; box-shadow: none; width: 100%; border-radius: 0; padding: 0; }}
            }}
        </style>
        <script>
            function printLetter() {{
                try {{ window.parent.document.title = "{pdf_file_name}"; }} catch(e) {{}}
                document.title = "{pdf_file_name}";
                window.print();
            }}
        </script>
    </head>
    <body>
        <div class="letter-box">
            <div class="header-flex">
                <div class="logo-box">{logo_html}</div>
                <div class="title-box">
                    <div class="title-l1">NARMADESHWAR VIKLANG VIKAAS MANAV SEVA TRUST</div>
                    <div class="title-l2">નર્મદેશ્વર વિકલાંગ વિકાસ માનવ સેવા ટ્રસ્ટ</div>
                    <div class="reg-no">Reg. No: {NGO_REG_NO}</div>
                </div>
            </div>
            
            <div class="meta-row">
                <div>જાવક નં: {letter_info.get('outward_no', 'N/A')}</div>
                <div>તારીખ: {fmt_date(letter_info.get('letter_date', 'N/A'))}</div>
            </div>

            <div class="recipient-box">
                પ્રતિ,<br>
                {letter_info.get('recipient', '').replace(chr(10), '<br>')}
            </div>

            <div>
                <span class="subject-box">વિષય: {letter_info.get('subject', '')}</span>
            </div>
            <div class="ref-box">
                સંદર્ભ નં: {letter_info.get('ref_no', 'N/A')}
            </div>

            <div class="body-content">
{letter_info.get('body_text', '')}
            </div>

            <div class="signature-box">
                પ્રમુખ / સેક્રેટરી<br>
                નર્મદેશ્વર વિકલાંગ વિકાસ માનવ સેવા ટ્રસ્ટ
            </div>

            <div style="clear: both;"></div>

            <button class="print-button" onclick="printLetter()">🖨️ પત્ર પ્રિન્ટ કરો / PDF સેવ કરો</button>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=650, scrolling=True)


# ==========================================
# 🎯 HEADER DESIGN (75% WIDTH, BALANCED & LEFT-ALIGNED)
# ==========================================
logo_b64_main = get_image_base64(LOGO_PATH)

if logo_b64_main:
    st.markdown(
        f"""
        <div class="header-wrapper">
            <img src="data:image/png;base64,{logo_b64_main}" />
            <div class="header-text-box">
                <p class="h-title-1">NARMADESHWAR</p>
                <p class="h-title-2">VIKLANG VIKAAS</p>
                <p class="h-title-3">MANAV SEVA TRUST</p>
                <p class="h-reg">Reg. No.: {NGO_REG_NO}</p>
                <div class="h-sub-text">
                    <span>જમણવાર બુકિંગ</span> | 
                    <span>દાન સ્વીકાર</span> | 
                    <span>ખર્ચ નોંધ</span> | 
                    <span>અનાજ સ્ટોક</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="header-wrapper" style="flex-direction: column !important;">
            <div class="header-text-box">
                <p class="h-title-1">NARMADESHWAR</p>
                <p class="h-title-2">VIKLANG VIKAAS</p>
                <p class="h-title-3">MANAV SEVA TRUST</p>
                <p class="h-reg">Reg. No.: {NGO_REG_NO}</p>
                <div class="h-sub-text">
                    <span>જમણવાર બુકિંગ</span> | 
                    <span>દાન સ્વીકાર</span> | 
                    <span>ખર્ચ નોંધ</span> | 
                    <span>અનાજ સ્ટોક</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ==========================================
# 🔒 TOP LOGIN & TOP NAVIGATION MENU
# ==========================================
st.markdown("### 🔑 સ્ટાફ / એડમિન લોગિન")
col_pwd, col_status = st.columns([2, 2])
with col_pwd:
    login_pwd = st.text_input(
        "પાસવર્ડ દાખલ કરો", 
        type="password", 
        key="top_login_pwd",
        label_visibility="collapsed",
        placeholder="પાસવર્ડ દાખલ કરો"
    )

if login_pwd == "ngo123":
    st.session_state["is_admin"] = True
    st.session_state["is_operator"] = True
    with col_status:
        st.success("🔓 માસ્ટર એડમિન મોડ સક્રિય!")
elif login_pwd == "op123":
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = True
    with col_status:
        st.success("🔓 ઓપરેટર મોડ સક્રિય!")
elif login_pwd != "":
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = False
    with col_status:
        st.error("❌ ખોટો પાસવર્ડ!")
else:
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = False

if st.session_state.get("is_admin", False):
    menu = [
        "🍲 જમણવાર બુકિંગ",
        "🎁 સામાન્ય દાન (Donation)",
        "💸 ખર્ચની નોંધ (Expenses)",
        "📦 અનાજ & સ્ટોક (Inventory)",
        "📜 લેટર ટાઇપિંગ અને જાવક",
        "📊 એડમિન & હિસાબ ડેશબોર્ડ",
    ]
elif st.session_state.get("is_operator", False):
    menu = [
        "🍲 જમણવાર બુકિંગ",
        "🎁 સામાન્ય દાન (Donation)",
        "💸 ખર્ચની નોંધ (Expenses)",
        "📦 અનાજ & સ્ટોક (Inventory)",
        "📜 લેટર ટાઇપિંગ અને જાવક",
        "📊 એડમિન & હિસાબ ડેશબોર્ડ",
    ]
else:
    menu = [
        "🍲 જમણવાર બુકિંગ",
        "🎁 સામાન્ય દાન (Donation)",
    ]

st.markdown("---")
choice = st.radio("📌 મુખ્ય મેનૂ", menu, horizontal=True)
st.markdown("---")

# ==========================================
# ૧. જમણવાર બુકિંગ મોડ્યુલ
# ==========================================
if choice == "🍲 જમણવાર બુકિંગ":
    st.subheader("📅 જમણવાર ઓનલાઈન બુકિંગ")

    if st.session_state.get("is_admin", False):
        st.info("🔓 એડમિન મોડ ચાલુ છે: તમે પાછલી (જૂની) તારીખ પણ પસંદ કરી શકો છો.")
        booking_date = st.date_input("૧. જમણવારની તારીખ પસંદ કરો *")
    else:
        booking_date = st.date_input("૧. જમણવારની તારીખ પસંદ કરો *", min_value=date.today())

    date_str = str(booking_date)

    cursor.execute("SELECT meal_types FROM bookings WHERE booking_date = ?", (date_str,))
    booked_records = cursor.fetchall()
    booked_meals = [m for row in booked_records if row[0] for m in row[0].split(", ")]

    st.write("### ૨. ઉપલબ્ધ જમણવાર પસંદ કરો (કાર્ડ પર ક્લિક કરો) *")

    if "selected_meals_list" not in st.session_state:
        st.session_state["selected_meals_list"] = []

    selected_meals = []

    c_card1, c_card2 = st.columns(2)
    card_cols = [c_card1, c_card2, c_card1, c_card2]

    for idx, meal in enumerate(ALL_MEALS):
        rate_display = int(MEAL_RATES[meal])
        is_booked = meal in booked_meals

        with card_cols[idx]:
            if is_booked:
                st.markdown(
                    f"""
                    <div style="background-color: #FEE2E2; border: 2px solid #EF4444; border-radius: 8px; padding: 14px; margin-bottom: 8px; text-align: center; opacity: 0.8; height: 95px; display: flex; flex-direction: column; justify-content: center;">
                        <h4 style="margin: 0; color: #991B1B; font-size: 14px;">❌ {meal}</h4>
                        <p style="margin: 4px 0 0 0; color: #B91C1C; font-weight: bold; font-size: 12px;">₹{rate_display} (બુક થયેલ)</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                is_selected = meal in st.session_state["selected_meals_list"]
                
                status_label = "✓ સિલેક્ટ થયેલ (હટાવવા ક્લિક કરો)" if is_selected else "સિલેક્ટ કરવા ક્લિક કરો"
                card_button_text = f"{meal}\n₹{rate_display}\n{status_label}"
                
                if st.button(card_button_text, key=f"card_btn_{idx}", type="primary" if is_selected else "secondary"):
                    if is_selected:
                        st.session_state["selected_meals_list"].remove(meal)
                    else:
                        st.session_state["selected_meals_list"].append(meal)
                    st.rerun()

    for meal in ALL_MEALS:
        if meal in st.session_state["selected_meals_list"] and meal not in booked_meals:
            selected_meals.append(meal)

    st.markdown("---")

    if selected_meals:
        meal_prep_type = st.radio(
            "૩. પ્રકાર *",
            ["૧. સંસ્થામાં બનાવવાનું છે", "૨. તૈયાર બનાવીને લાવશે"],
        )

        prefix_options = ["શ્રી", "સ્વ.", "ગં.સ્વ.", "શ્રીમતી", "કુ."]

        c1, c2 = st.columns(2)
        with c1:
            col_p1, col_n1 = st.columns([1, 2.5])
            with col_p1:
                d_prefix = st.selectbox("પ્રીફિક્સ", prefix_options, key="p_donor")
            with col_n1:
                raw_donor_name = st.text_input("૪. દાતાશ્રીનું નામ *")

            donor_name = f"{d_prefix} {raw_donor_name.upper()}".strip() if raw_donor_name else ""
            donor_phone = st.text_input("૫. મોબાઈલ નંબર *", max_chars=10, placeholder="9876543210")

        with c2:
            col_p2, col_n2 = st.columns([1, 2.5])
            with col_p2:
                s_prefix = st.selectbox("પ્રીફિક્સ", prefix_options, key="p_service")
            with col_n2:
                raw_service_name = st.text_input("૬. જેમના નામે સેવા આપવી હોય તેમનું નામ *", value=raw_donor_name)

            service_for_name = f"{s_prefix} {raw_service_name.upper()}".strip() if raw_service_name else ""

        payment_status = "N/A"
        payment_type = "N/A"
        utr_number = "N/A"
        final_amount = 0.0

        if meal_prep_type == "૧. સંસ્થામાં બનાવવાનું છે":
            st.markdown("---")
            st.write("### 💳 પેમેન્ટની માહિતી")

            p_col1, p_col2 = st.columns(2)

            with p_col1:
                payment_status = st.radio(
                    "Payment આવી ગયેલ છે? *",
                    ["Yes (આવી ગયેલ છે)", "No (બાકી છે)"],
                    horizontal=True,
                )
                payment_type = st.selectbox(
                    "Payment Type (પેમેન્ટનો પ્રકાર) *",
                    ["Cash (રોકડ)", "Online (UPI / QR)", "Bank Transfer"],
                )

            calculated_amt = sum(MEAL_RATES[m] for m in selected_meals)

            with p_col2:
                final_amount = st.number_input(
                    "જમણવારની રકમ (₹) *",
                    value=float(calculated_amt),
                    step=50.0,
                    format="%.2f",
                )
                if payment_type in ["Online (UPI / QR)", "Bank Transfer"]:
                    utr_number = st.text_input(
                        "UTR / Ref No (ઓપ્શનલ)",
                        placeholder="12 અંકનો ટ્રાન્ઝેક્શન ID",
                    )
                    if not utr_number:
                        utr_number = "Not Provided"

        st.markdown("<br>", unsafe_allow_html=True)
        save_btn = st.button("💾 બુકિંગ સેવ કરો", type="primary")

        if save_btn:
            if not raw_donor_name or not donor_phone:
                st.error("❌ કૃપા કરીને દાતાશ્રીનું નામ અને મોબાઈલ નંબર દાખલ કરો.")
            else:
                meals_str = ", ".join(selected_meals)

                cursor.execute(
                    """
                    INSERT INTO bookings (donor_name, phone, service_for_name, booking_date, meal_types, meal_prep_type, amount, payment_status, payment_type, utr_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        donor_name,
                        donor_phone,
                        service_for_name,
                        date_str,
                        meals_str,
                        meal_prep_type,
                        final_amount,
                        payment_status,
                        payment_type,
                        utr_number,
                    ),
                )
                conn.commit()
                last_id = cursor.lastrowid
                st.success("🎉 જમણવાર બુકિંગ સફળતાપૂર્વક સેવ થઈ ગયું છે!")

                st.session_state["selected_meals_list"] = []

                booking_dict = {
                    "id": last_id,
                    "donor_name": donor_name,
                    "phone": donor_phone,
                    "service_for_name": service_for_name,
                    "booking_date": date_str,
                    "meal_types": meals_str,
                    "meal_prep_type": meal_prep_type,
                    "amount": final_amount,
                    "payment_status": payment_status,
                    "payment_type": payment_type,
                }

                saved_path = auto_save_pdf_to_folder(booking_dict)
                if saved_path:
                    st.toast(f"💾 PDF Auto-saved: {saved_path}", icon="✅")

                st.write("### 📄 જમણવાર પાવતી (Receipt)")
                render_html_receipt(booking_dict)

                msg = (
                    f"નમસ્તે NARMADESHWAR VIKLANG VIKAAS MANAV SEVA TRUST,%0A%0A"
                    f"મેં જમણવાર બુક કર્યો છે:%0A"
                    f"👤 દાતાશ્રી: {donor_name}%0A"
                    f"🙏 સેવા નામ: {service_for_name}%0A"
                    f"📅 તારીખ: {fmt_date(date_str)}%0A"
                    f"🍲 જમણવાર: {meals_str}%0A"
                    f"🥣 પ્રકાર: {meal_prep_type}%0A"
                    f"💰 રકમ: ₹{final_amount}%0A"
                    f"💳 પેમેન્ટ સ્ટેટસ: {payment_status}"
                )

                wa_url = f"https://api.whatsapp.com/send?phone={NGO_PHONE}&text={msg}"
                st.markdown(
                    f"""
                    <a href="{wa_url}" target="_blank">
                        <button style="background-color: #25D366; color: white; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 10px; font-size: 16px;">
                            📲 WhatsApp પર કન્ફર્મેશન મોકલો
                        </button>
                    </a>
                """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("💡 કૃપા કરીને ઉપરના કાર્ડ્સમાંથી કોઈપણ જમણવાર પસંદ કરો.")

# ==========================================
# ૨. સામાન્ય દાન (Donation)
# ==========================================
elif choice == "🎁 સામાન્ય દાન (Donation)":
    st.subheader("🎁 સામાન્ય દાન સ્વીકાર ફોર્મ")
    prefix_options = ["શ્રી", "સ્વ.", "ગં.સ્વ.", "શ્રીમતી", "કુ."]

    with st.form("donation_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            c_dp, c_dn = st.columns([1, 2.5])
            with c_dp:
                don_prefix = st.selectbox("પ્રીફિક્સ", prefix_options)
            with c_dn:
                raw_d_name = st.text_input("દાતાનું પૂરૂં નામ *")
            d_name = f"{don_prefix} {raw_d_name.upper()}".strip() if raw_d_name else ""
            d_phone = st.text_input("મોબાઈલ નંબર", max_chars=10)
            d_type = st.selectbox(
                "દાનનો પ્રકાર", ["સામાન્ય દાન (General)", "વિકલાંગ સેવા દાન", "અનાજ દાન", "અન્ય"]
            )
        with col2:
            d_amount = st.number_input("દાનની રકમ (₹) *", min_value=1.0)
            d_mode = st.selectbox("પેમેન્ટ મોડ", ["Cash (રોકડ)", "Online (UPI / QR)", "Bank Transfer"])
            d_utr = st.text_input("UTR / Receipt No (ઓપ્શનલ)", placeholder="ઓપ્શનલ Ref ID")

        submit_d = st.form_submit_button("💾 દાન સેવ કરો")

        if submit_d:
            if not raw_d_name or d_amount <= 0:
                st.error("❌ કૃપા કરીને દાતાનું નામ અને યોગ્ય રકમ નાખો.")
            else:
                cursor.execute(
                    """
                    INSERT INTO donations (donor_name, phone, donation_type, amount, payment_mode, utr_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (d_name, d_phone, d_type, d_amount, d_mode, d_utr if d_utr else "N/A"),
                )
                conn.commit()
                st.success(f"✅ {d_name} નું ₹{d_amount} નું દાન નોંધાઈ ગયું છે. ધન્યવાદ!")

# ==========================================
# ૩. ખર્ચ મેનેજમેન્ટ (Expenses)
# ==========================================
elif choice == "💸 ખર્ચની નોંધ (Expenses)":
    st.subheader("💸 NGO રોજિંદો ખર્ચ")

    with st.form("expense_form", clear_on_submit=True):
        e_date = st.date_input("ખર્ચની તારીખ")
        e_cat = st.selectbox(
            "ખર્ચનો પ્રકાર",
            ["અનાજ / કરિયાણું / શાકભાજી", "વિકલાંગ સેવા સાધનો / મદદ", "રસોઈયા / સ્ટાફ પગાર", "ગેસ સિલિન્ડર / લાઈટ બિલ", "ટ્રાન્સપોર્ટ / ભાડું", "અન્ય પરચુરણ ખર્ચ"],
        )
        e_desc = st.text_input("ખર્ચની વિગત / કોને ચૂકવ્યા?")
        e_amount = st.number_input("રકમ (₹) *", min_value=1.0)

        submit_e = st.form_submit_button("💾 ખર્ચ સેવ કરો")

        if submit_e:
            if not e_desc or e_amount <= 0:
                st.error("❌ વિગત અને રકમ સાચી દાખલ કરો.")
            else:
                cursor.execute(
                    """
                    INSERT INTO expenses (expense_date, category, description, amount)
                    VALUES (?, ?, ?, ?)
                """,
                    (str(e_date), e_cat, e_desc.upper(), e_amount),
                )
                conn.commit()
                st.success("✅ ખર્ચ સફળતાપૂર્વક નોંધાઈ ગયો.")

# ==========================================
# ૪. સ્ટોક મેનેજમેન્ટ (Stock In / Out)
# ==========================================
elif choice == "📦 અનાજ & સ્ટોક (Inventory)":
    st.subheader("📦 અનાજ અને વસ્તુઓનો સ્ટોક (Stock In/Out)")
    tab1, tab2 = st.tabs(["➕ નવી સ્ટોક એન્ટ્રી", "📊 લાઈવ સ્ટોક સ્ટેટસ"])

    with tab1:
        with st.form("stock_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                item_name = st.text_input("વસ્તુનું નામ *", placeholder="દા.ત. ઘઉં, ચોખા, સીંગતેલ")
                t_type = st.radio("પ્રકાર *", ["IN (આવક - દાન/ખરીદી)", "OUT (જાવક - રસોડામાં વપરાશ)"])
                qty = st.number_input("જથ્થો *", min_value=0.1)
            with col2:
                unit = st.selectbox("એકમ (Unit)", ["કિલો (Kg)", "કટ્ટા/ગુણ", "ડબ્બા", "લિટર", "નંગ"])
                i_date = st.date_input("એન્ટ્રી તારીખ")
                remarks = st.text_input("નોંધ (ઓપ્શનલ)")

            submit_s = st.form_submit_button("💾 સ્ટોક સેવ કરો")

            if submit_s:
                if not item_name or qty <= 0:
                    st.error("❌ કૃપા કરીને વસ્તુનું નામ અને સાચો જથ્થો લખો.")
                else:
                    trans_code = "IN" if "IN" in t_type else "OUT"
                    cursor.execute(
                        """
                        INSERT INTO inventory (item_name, trans_type, quantity, unit, entry_date, remarks)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (item_name.strip().upper(), trans_code, qty, unit, str(i_date), remarks.upper()),
                    )
                    conn.commit()
                    st.success("✅ સ્ટોક એન્ટ્રી સફળતાપૂર્વક થઈ ગઈ!")

    with tab2:
        st.write("### 📈 વર્તમાન સ્ટોક સ્ટેટસ")
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        if not df_inv.empty:
            summary = []
            for item in df_inv["item_name"].unique():
                item_data = df_inv[df_inv["item_name"] == item]
                total_in = item_data[item_data["trans_type"] == "IN"]["quantity"].sum()
                total_out = item_data[item_data["trans_type"] == "OUT"]["quantity"].sum()
                balance = total_in - total_out
                unit_name = item_data["unit"].iloc[-1]
                summary.append({"વસ્તુનું નામ": item, "કુલ આવક (IN)": total_in, "કુલ જાવક (OUT)": total_out, "હાલનો સ્ટોક (Balance)": balance, "એકમ": unit_name})
            st.dataframe(pd.DataFrame(summary), use_container_width=True)
        else:
            st.info("હજુ સુધી કોઈ સ્ટોક એન્ટ્રી કરવામાં આવી નથી.")

# ==========================================
# ૫. 📜 લેટર ટાઇપિંગ અને જાવક મોડ્યુલ
# ==========================================
elif choice == "📜 લેટર ટાઇપિંગ અને જાવક":
    st.subheader("📜 સત્તાવાર પત્ર (Letter) ટાઇપિંગ અને જાવક વ્યવસ્થાપન")
    
    tab_L1, tab_L2 = st.tabs(["✍️ નવો પત્ર બનાવો", "📂 જૂના પત્રોનું લિસ્ટ (Index) & એડિટ"])

    with tab_L1:
        with st.form("letter_form", clear_on_submit=True):
            col_l1, col_l2, col_l3 = st.columns(3)
            with col_l1:
                outward_no = st.text_input("જાવક નંબર (Outward No.) *", placeholder="દા.ત. 101/2026")
            with col_l2:
                ref_no = st.text_input("સંદર્ભ નંબર (Ref No.)", placeholder="દા.ત. REF-55")
            with col_l3:
                letter_date = st.date_input("પત્રની તારીખ")

            recipient = st.text_area("પ્રતિ (Recipient Address) *", placeholder="શ્રીમાન અધિકારીશ્રી,\nગ્રામ પંચાયત કાર્યાલય,...")
            subject = st.text_input("વિષય (Subject) *", placeholder="દિવ્યાંગ સહાય અર્થે બાબત...")
            body_text = st.text_area("પત્રનું મુખ્ય લખાણ (Body Text) *", height=200, placeholder="સવિનય સાથ જણાવવાનું કે...")

            submit_letter = st.form_submit_button("💾 પત્ર સેવ કરો અને જુઓ")

            if submit_letter:
                if not outward_no or not recipient or not subject or not body_text:
                    st.error("❌ કૃપા કરીને જાવક નંબર, પ્રતિ, વિષય અને પત્રનું લખાણ અવશ્ય ભરો.")
                else:
                    cursor.execute(
                        """
                        INSERT INTO letters (outward_no, ref_no, letter_date, recipient, subject, body_text)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (outward_no.upper(), ref_no.upper(), str(letter_date), recipient, subject, body_text),
                    )
                    conn.commit()
                    last_letter_id = cursor.lastrowid
                    st.success("🎉 પત્ર સફળતાપૂર્વક સેવ થઈ ગયો છે!")

                    letter_dict = {
                        "id": last_letter_id,
                        "outward_no": outward_no.upper(),
                        "ref_no": ref_no.upper(),
                        "letter_date": str(letter_date),
                        "recipient": recipient,
                        "subject": subject,
                        "body_text": body_text,
                    }

                    st.markdown("---")
                    st.write("### 📄 પત્ર પ્રિવ્યુ (Letter Preview)")
                    render_html_letter(letter_dict)

                    w_msg = f"નમસ્તે, જાવક નં: {outward_no.upper()} | વિષય: {subject}"
                    wa_letter_url = f"https://api.whatsapp.com/send?phone={NGO_PHONE}&text={urllib.parse.quote(w_msg)}"
                    st.markdown(
                        f"""
                        <a href="{wa_letter_url}" target="_blank">
                            <button style="background-color: #25D366; color: white; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 10px; font-size: 16px;">
                                📲 WhatsApp પર પત્રની વિગત મોકલો
                            </button>
                        </a>
                        """,
                        unsafe_allow_html=True,
                    )

    with tab_L2:
        st.write("### 📂 સેવ થયેલા તમામ પત્રોનું ઇન્ડેક્સ (Index)")
        cursor.execute("SELECT id, outward_no, ref_no, letter_date, recipient, subject FROM letters ORDER BY id DESC")
        all_letters = cursor.fetchall()

        if all_letters:
            letter_options = {f"જાવક નં: {l[1]} | તારીખ: {fmt_date(l[3])} | વિષય: {l[5]}": l[0] for l in all_letters}
            
            selected_l_label = st.selectbox(
                "પ્રિન્ટ અથવા એડિટ કરવા માટે પત્ર પસંદ કરો:", 
                list(letter_options.keys()), 
                key="letter_index_selectbox"
            )
            sel_l_id = letter_options[selected_l_label]

            if sel_l_id:
                cursor.execute("SELECT id, outward_no, ref_no, letter_date, recipient, subject, body_text FROM letters WHERE id = ?", (sel_l_id,))
                l_rec = cursor.fetchone()
                if l_rec:
                    l_dict = {
                        "id": l_rec[0],
                        "outward_no": l_rec[1],
                        "ref_no": l_rec[2],
                        "letter_date": l_rec[3],
                        "recipient": l_rec[4],
                        "subject": l_rec[5],
                        "body_text": l_rec[6],
                    }
                    
                    action_mode = st.radio(
                        "ક્રિયા પસંદ કરો:", 
                        ["📄 પત્ર જુઓ / પ્રિન્ટ કરો", "✏️ પત્ર એડિટ કરો"], 
                        horizontal=True, 
                        key=f"action_mode_{sel_l_id}"
                    )
                    
                    if action_mode == "📄 પત્ર જુઓ / પ્રિન્ટ કરો":
                        render_html_letter(l_dict)
                    else:
                        st.write("#### ✍️ પત્ર સુધારો (Edit Letter)")
                        with st.form(f"edit_letter_form_{sel_l_id}"):
                            e_outward = st.text_input("જાવક નંબર *", value=l_dict["outward_no"])
                            e_ref = st.text_input("સંદર્ભ નંબર", value=l_dict["ref_no"])
                            
                            try:
                                parsed_date = datetime.strptime(l_dict["letter_date"], "%Y-%m-%d").date()
                            except:
                                parsed_date = date.today()
                            e_date = st.date_input("પત્રની તારીખ", value=parsed_date)
                            
                            e_recipient = st.text_area("પ્રતિ *", value=l_dict["recipient"])
                            e_subject = st.text_input("વિષય *", value=l_dict["subject"])
                            e_body = st.text_area("પત્રનું મુખ્ય લખાણ *", value=l_dict["body_text"], height=200)

                            update_submit = st.form_submit_button("💾 ફેરફારો સેવ કરો (Update)")
                            if update_submit:
                                if not e_outward or not e_recipient or not e_subject or not e_body:
                                    st.error("❌ કૃપા કરીને તમામ જરૂરી ખાના ભરો.")
                                else:
                                    cursor.execute("""
                                        UPDATE letters 
                                        SET outward_no = ?, ref_no = ?, letter_date = ?, recipient = ?, subject = ?, body_text = ?
                                        WHERE id = ?
                                    """, (e_outward.upper(), e_ref.upper(), str(e_date), e_recipient, e_subject, e_body, sel_l_id))
                                    conn.commit()
                                    st.success("✅ પત્ર સફળતાપૂર્વક અપડેટ થઈ ગયો છે!")
        else:
            st.info("હજુ સુધી કોઈ પત્ર સેવ કરવામાં આવ્યો નથી.")

# ==========================================
# ૬. એડમિન & ઓપરેટર ડેશબોર્ડ
# ==========================================
elif choice == "📊 એડમિન & હિસાબ ડેશબોર્ડ":
    st.subheader("🔒 માસ્ટર એડમિન પેનલ")

    c_jmn = cursor.execute("SELECT SUM(amount) FROM bookings").fetchone()[0] or 0.0
    c_don = cursor.execute("SELECT SUM(amount) FROM donations").fetchone()[0] or 0.0
    tot_inc = c_jmn + c_don
    tot_exp = cursor.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
    net_bal = tot_inc - tot_exp

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🍲 જમણવાર આવક", f"₹ {c_jmn:,.2f}")
    m2.metric("🎁 સામાન્ય દાન", f"₹ {c_don:,.2f}")
    m3.metric("📤 કુલ ખર્ચ", f"₹ {tot_exp:,.2f}")
    m4.metric("💵 હાથ પર બાકી (Net)", f"₹ {net_bal:,.2f}")

    st.markdown("---")

    st.write("### 📅 જમણવારની યાદી (Check & Inform Donors)")

    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        selected_view_date = st.date_input("**ચોક્કસ તારીખ પસંદ કરો અને જમણવાર જુઓ:**", value=date.today())
    with col_d2:
        st.write("")
        st.write("")  
        if st.button("🔄 યાદી જુઓ", type="primary"):
            st.session_state["view_date_selected"] = True

    view_date_str = str(selected_view_date)

    cursor.execute("""
        SELECT id, donor_name, phone, service_for_name, meal_types, meal_prep_type, amount 
        FROM bookings WHERE booking_date = ?
    """, (view_date_str,))
    selected_date_bookings = cursor.fetchall()

    if selected_date_bookings:
        st.info(f"📌 **{fmt_date(view_date_str)}** ના કુલ {len(selected_date_bookings)} જમણવાર બુક થયેલ છે.")
        
        df_view = pd.DataFrame(selected_date_bookings, columns=["ID", "દાતાશ્રી", "મોબાઈલ", "સેવા નામ", "જમણવાર", "પ્રકાર", "રકમ (₹)"])
        st.dataframe(df_view, use_container_width=True)

        date_msg = f"નમસ્તે NARMADESHWAR TRUST,%0A%0A**{fmt_date(view_date_str)}** ના જમણવારની યાદી:%0A"
        for b in selected_date_bookings:
            date_msg += f"👤 {b[1]} (મોબાઈલ: {b[2]}) | {b[4]} | રકમ: ₹{b[6]:,.2f}%0A"
        
        wa_link = f"https://api.whatsapp.com/send?phone={NGO_PHONE}&text={date_msg}"
        st.markdown(
            f"""
            <a href="{wa_link}" target="_blank">
                <button style="background-color: #25D366; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 5px;">
                    📲 આ તારીખના બધા દાતાઓને WhatsApp મોકલો
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"❌ **{fmt_date(view_date_str)}** ના રોજ કોઈ જમણવાર બુક થયેલ નથી.")

    st.markdown("---")

    today_str = str(date.today())
    cursor.execute("""
        SELECT id, donor_name, phone, service_for_name, meal_types, meal_prep_type, amount 
        FROM bookings WHERE booking_date = ?
    """, (today_str,))
    today_bookings = cursor.fetchall()

    st.write(f"### 🟢 આજનો જમણવાર ({fmt_date(today_str)})")
    if today_bookings:
        df_today = pd.DataFrame(today_bookings, columns=["ID", "દાતાશ્રી", "મોબાઈલ", "સેવા નામ", "જમણવાર", "પ્રકાર", "રકમ (₹)"])
        st.dataframe(df_today, use_container_width=True)
        
        today_msg = f"નમસ્તે NARMADESHWAR TRUST,%0A%0A**આજ ({fmt_date(today_str)})** ના જમણવારની યાદી:%0A"
        for b in today_bookings:
            today_msg += f"👤 {b[1]} (મોબાઈલ: {b[2]}) | {b[4]} | રકમ: ₹{b[6]:,.2f}%0A"
        
        wa_link_today = f"https://api.whatsapp.com/send?phone={NGO_PHONE}&text={today_msg}"
        st.markdown(
            f"""
            <a href="{wa_link_today}" target="_blank">
                <button style="background-color: #25D366; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 5px;">
                    📲 આજના બધા દાતાઓને WhatsApp મોકલો
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.success("✅ આજે કોઈ જમણવાર બુક થયેલ નથી.")

    st.markdown("---")

    st.write("### 🔵 આગામી ૩ દિવસના જમણવાર")
    next_dates = [(date.today() + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(3)]
    
    for nd in next_dates:
        cursor.execute("""
            SELECT id, donor_name, phone, service_for_name, meal_types, meal_prep_type, amount 
            FROM bookings WHERE booking_date = ?
        """, (nd,))
        nd_bookings = cursor.fetchall()
        
        st.write(f"**📅 {fmt_date(nd)}**")
        if nd_bookings:
            df_nd = pd.DataFrame(nd_bookings, columns=["ID", "દાતાશ્રી", "મોબાઈલ", "સેવા નામ", "જમણવાર", "પ્રકાર", "રકમ (₹)"])
            st.dataframe(df_nd, use_container_width=True)
        else:
            st.caption(f"👉 {fmt_date(nd)} ના રોજ કોઈ બુકિંગ નથી.")
        
    st.markdown("---")

    st.write("### 📄 જૂની પાવતી / રસીદ જોઈને પ્રિન્ટ કરો")
    cursor.execute("SELECT id, donor_name, booking_date FROM bookings ORDER BY id DESC")
    all_bookings = cursor.fetchall()

    if all_bookings:
        booking_options = {f"રસીદ નં #{b[0]} - {b[1]} (તારીખ: {fmt_date(b[2])})": b[0] for b in all_bookings}
        selected_receipt_label = st.selectbox("પ્રિન્ટ કરવા માટે જૂની રસીદ પસંદ કરો:", list(booking_options.keys()))
        selected_id = booking_options[selected_receipt_label]

        if selected_id:
            cursor.execute(
                "SELECT id, donor_name, phone, service_for_name, booking_date, meal_types, meal_prep_type, amount, payment_status, payment_type FROM bookings WHERE id = ?",
                (selected_id,),
            )
            rec = cursor.fetchone()
            if rec:
                receipt_dict = {
                    "id": rec[0],
                    "donor_name": rec[1],
                    "phone": rec[2],
                    "service_for_name": rec[3],
                    "booking_date": rec[4],
                    "meal_types": rec[5],
                    "meal_prep_type": rec[6],
                    "amount": rec[7],
                    "payment_status": rec[8],
                    "payment_type": rec[9],
                }
                render_html_receipt(receipt_dict)
    else:
        st.info("હજુ સુધી કોઈ બુકિંગ નોંધાયેલ નથી.")

    st.markdown("---")
    st.write("### 📋 જમણવાર બુકિંગ લિસ્ટ (સંપૂર્ણ)")
    df_b = pd.read_sql_query(
        "SELECT id, donor_name AS 'દાતાશ્રી', service_for_name AS 'જેમના નામે સેવા', phone AS 'મોબાઈલ', booking_date AS 'તારીખ', meal_types AS 'જમણવાર', meal_prep_type AS 'પ્રકાર', amount AS 'રકમ (₹)', payment_status AS 'Pay Status', payment_type AS 'Pay Type' FROM bookings ORDER BY id DESC",
        conn,
    )
    if not df_b.empty and 'તારીખ' in df_b.columns:
        df_b['તારીખ'] = df_b['તારીખ'].apply(fmt_date)
    st.dataframe(df_b, use_container_width=True)

    st.markdown("---")
    st.write("### 📥 ડેટા ડાઉનલોડ કરો")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.read_sql_query("SELECT * FROM bookings", conn).to_excel(writer, sheet_name="Jamanvar", index=False)
        pd.read_sql_query("SELECT * FROM donations", conn).to_excel(writer, sheet_name="Donations", index=False)
        pd.read_sql_query("SELECT * FROM expenses", conn).to_excel(writer, sheet_name="Expenses", index=False)
        pd.read_sql_query("SELECT * FROM inventory", conn).to_excel(writer, sheet_name="Inventory", index=False)
        pd.read_sql_query("SELECT * FROM letters", conn).to_excel(writer, sheet_name="Letters", index=False)

    st.download_button(
        label="📥 તમામ ડેટા Excel માં ડાઉનલોડ કરો",
        data=buffer.getvalue(),
        file_name="ngo_master_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
