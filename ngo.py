import base64
from datetime import date, datetime
import io
import os
import sqlite3
import urllib.parse
import pandas as pd
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

from reportlab.lib.pagesizes import A6
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
conn.commit()

# ==========================================
# NGO CONFIGURATION & RELATIVE PATHS
# ==========================================
NGO_NAME = "નર્મદેશ્વર વિકલાંગ વિકાસ માનવ સેવા ટ્રસ્ટ"
NGO_REG_NO = "F/5155/Mehsana (એફ/૫૧૫૫/મહેસાણા)"
NGO_PHONE = "917377174779"

# 🖼️ Dynamic Logo Path Detection
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

# 📁 Dynamic Receipts Directory
BASE_DIR = os.getcwd()
RECEIPTS_DIR = os.path.join(BASE_DIR, "Receipts")
try:
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
except Exception:
    RECEIPTS_DIR = "/tmp/Receipts"
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def get_image_base64(image_path):
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return ""
    return ""


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
    initial_sidebar_state="expanded",
)

# 🎨 PERFECT RESPONSIVE & CLICKABLE MOBILE/DESKTOP STYLING
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;600;700;800;900&display=swap');

    p, label, input, button, h1, h2, h3, h4, .stMarkdown, .stSelectbox, .stRadio, .stCheckbox {
        font-family: 'Noto Sans Gujarati', sans-serif !important;
    }

    /* 🔠 Auto Capitalize text inputs */
    input[type="text"] {
        text-transform: uppercase !important;
    }

    footer, #MainMenu {
        display: none !important;
    }

    .main .block-container {
        max-width: 650px !important;
        margin: 0 auto !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }

    /* 📱 Header Side-by-Side Flex Layout (Mobile & Desktop) */
    .header-flex-box {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 12px !important;
        width: 100% !important;
        margin-bottom: 10px !important;
    }

    .header-logo-img {
        height: 75px !important;
        width: auto !important;
        object-fit: contain !important;
        flex-shrink: 0 !important;
    }

    .header-title-box {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        line-height: 1.15 !important;
        text-align: left !important;
    }

    .h-l1 { color: #16A34A !important; margin: 0 !important; font-size: 20px !important; font-weight: 900 !important; letter-spacing: 1px !important; }
    .h-l2 { color: #0284C7 !important; margin: 0 !important; font-size: 16px !important; font-weight: 800 !important; letter-spacing: 1px !important; }
    .h-l3 { color: #1E3A8A !important; margin: 0 !important; font-size: 16px !important; font-weight: 800 !important; letter-spacing: 1px !important; }
    .h-reg { color: #4B5563 !important; margin: 2px 0 0 0 !important; font-size: 10.5px !important; font-weight: 700 !important; }

    /* 🎯 Fix Desktop Mode Checkbox Click Issue */
    .stCheckbox {
        pointer-events: auto !important;
        cursor: pointer !important;
    }
    .stCheckbox label {
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        user-select: none !important;
    }

    @media (max-width: 768px) {
        .h-l1 { font-size: 16px !important; }
        .h-l2 { font-size: 13.5px !important; }
        .h-l3 { font-size: 13.5px !important; }
        .h-reg { font-size: 9.5px !important; }
        .header-logo-img { height: 60px !important; }

        /* Keep Checkbox columns side-by-side on mobile */
        [data-testid="column"] {
            width: 50% !important;
            flex: 1 1 50% !important;
            min-width: 45% !important;
        }

        .stCheckbox label {
            font-size: 13px !important;
        }

        .stButton button {
            width: 100% !important;
            font-size: 16px !important;
            padding: 12px !important;
        }
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 📄 AUTO-SAVE BACKEND PDF FUNCTION (A6 SMALL SIZE)
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
            ("Meal Date:", str(booking_info["booking_date"])),
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
            
            * {{
                box-sizing: border-box;
            }}
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
            .logo-box {{
                flex-shrink: 0;
            }}
            .receipt-logo {{
                height: 60px;
                width: auto;
            }}
            .title-box {{
                text-align: left;
                display: flex;
                flex-direction: column;
                justify-content: center;
                line-height: 1.15;
            }}
            .title-l1 {{
                color: #16A34A;
                font-size: 14px;
                font-weight: 900;
                letter-spacing: 1px;
            }}
            .title-l2 {{
                color: #0284C7;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
            }}
            .title-l3 {{
                color: #1E3A8A;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
            }}
            .reg-no {{
                color: #4b5563;
                font-size: 9px;
                font-weight: 700;
                margin-top: 2px;
            }}
            .receipt-nametag {{
                color: #1d4ed8;
                margin-top: 1px;
                font-size: 11px;
                font-weight: 700;
                word-break: break-word;
            }}
            .row {{
                display: flex;
                justify-content: space-between;
                padding: 4px 6px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 11px;
                gap: 6px;
            }}
            .row:nth-child(even) {{
                background-color: #f8fafc;
            }}
            .label {{
                font-weight: 600;
                color: #1e3a8a;
                flex-shrink: 0;
            }}
            .value {{
                color: #111827;
                text-align: right;
                font-weight: 500;
                word-break: break-word;
                text-transform: uppercase;
            }}
            .total-row {{
                background-color: #eff6ff !important;
                font-weight: 700;
                color: #1e3a8a;
                font-size: 12px;
                border-top: 1px solid #1e3a8a;
                border-bottom: 1px solid #1e3a8a;
            }}
            .footer {{
                text-align: center;
                margin-top: 8px;
                color: #059669;
                font-weight: 600;
                font-size: 10px;
                line-height: 1.3;
            }}
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
                font-family: 'Noto Sans Gujarati', sans-serif;
            }}
            .print-button:hover {{
                background-color: #1d4ed8;
            }}

            @media print {{
                @page {{
                    size: A6 portrait;
                    margin: 0;
                }}
                .print-button {{ display: none; }}
                body {{ background-color: #ffffff; padding: 0; margin: 0; }}
                .receipt-box {{
                    border: 1px solid #000;
                    box-shadow: none;
                    max-width: 100%;
                    width: 100%;
                    border-radius: 0;
                }}
            }}
        </style>
        <script>
            function printReceipt() {{
                try {{
                    window.parent.document.title = "{pdf_file_name}";
                }} catch(e) {{}}
                document.title = "{pdf_file_name}";
                window.print();
            }}
        </script>
    </head>
    <body>
        <div class="receipt-box">
            <div class="header-flex">
                <div class="logo-box">
                    {logo_html}
                </div>
                <div class="title-box">
                    <div class="title-l1">NARMADESHWAR</div>
                    <div class="title-l2">VIKLANG VIKAAS</div>
                    <div class="title-l3">MANAV SEVA TRUST</div>
                    <div class="reg-no">Reg. No: {NGO_REG_NO}</div>
                    <div class="receipt-nametag">Receipt No: #{booking_info.get('id', 'N/A')}</div>
                </div>
            </div>
            
            <div class="row">
                <span class="label">પાવતી નં / No:</span>
                <span class="value">#{booking_info.get('id', 'N/A')}</span>
            </div>
            <div class="row">
                <span class="label">તારીખ / Date:</span>
                <span class="value">{datetime.now().strftime('%d-%m-%Y')}</span>
            </div>
            <div class="row">
                <span class="label">દાતાશ્રી / Donor:</span>
                <span class="value">{booking_info['donor_name']}</span>
            </div>
            <div class="row">
                <span class="label">મોબાઈલ / Mobile:</span>
                <span class="value">{booking_info['phone']}</span>
            </div>
            <div class="row">
                <span class="label">સેવા નામ / Service For:</span>
                <span class="value">{booking_info['service_for_name']}</span>
            </div>
            <div class="row">
                <span class="label">જમણવાર તારીખ:</span>
                <span class="value">{booking_info['booking_date']}</span>
            </div>
            <div class="row">
                <span class="label">જમણવાર / Meal:</span>
                <span class="value">{booking_info['meal_types']}</span>
            </div>
            <div class="row">
                <span class="label">પ્રકાર / Prep Type:</span>
                <span class="value">{booking_info['meal_prep_type']}</span>
            </div>
            <div class="row total-row">
                <span>રકમ / Amount:</span>
                <span>₹ {booking_info['amount']:,.2f}</span>
            </div>
            <div class="row">
                <span class="label">પેમેન્ટ / Payment:</span>
                <span class="value">{booking_info['payment_type']} ({booking_info['payment_status']})</span>
            </div>

            <div class="footer">
                Thank you for your noble support!<br>આપના માનવસેવા યોગદાન બદલ આભાર!
            </div>

            <button class="print-button" onclick="printReceipt()">🖨️ પાવતી પ્રિન્ટ કરો / PDF સેવ કરો</button>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=530, scrolling=True)


# ==========================================
# 🎯 HEADER DESIGN (SIDE-BY-SIDE SIDEWAYS)
# ==========================================
logo_b64_main = get_image_base64(LOGO_PATH)

if logo_b64_main:
    st.markdown(
        f"""
        <div class="header-flex-box">
            <img class="header-logo-img" src="data:image/png;base64,{logo_b64_main}" />
            <div class="header-title-box">
                <h1 class="h-l1">NARMADESHWAR</h1>
                <h1 class="h-l2">VIKLANG VIKAAS</h1>
                <h1 class="h-l3">MANAV SEVA TRUST</h1>
                <p class="h-reg">Reg. No.: {NGO_REG_NO}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="header-flex-box">
            <div class="header-title-box" style="text-align: center;">
                <h1 class="h-l1">NARMADESHWAR</h1>
                <h1 class="h-l2">VIKLANG VIKAAS</h1>
                <h1 class="h-l3">MANAV SEVA TRUST</h1>
                <p class="h-reg">Reg. No.: {NGO_REG_NO}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    "<p style='text-align: center; color: #4B5563; font-size: 13.5px; font-weight: bold; margin-top: 5px; margin-bottom: 15px;'>જમણવાર બુકિંગ | દાન સ્વીકાર | ખર્ચ નોંધ | અનાજ સ્ટોક મેનેજમેન્ટ</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# ==========================================
# 🔒 LOGIN SYSTEM
# ==========================================
st.sidebar.markdown("### 🔑 સ્ટાફ / એડમિન લોગિન")
login_pwd = st.sidebar.text_input(
    "પાસવર્ડ દાખલ કરો", type="password", key="side_login_pwd"
)

if login_pwd == "ngo123":
    st.session_state["is_admin"] = True
    st.session_state["is_operator"] = True
    st.sidebar.success("🔓 માસ્ટર એડમિન મોડ!")
elif login_pwd == "op123":
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = True
    st.sidebar.success("🔓 ઓપરેટર મોડ સક્રિય!")
elif login_pwd != "":
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = False
    st.sidebar.error("❌ ખોટો પાસવર્ડ!")
else:
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = False

st.sidebar.markdown("---")

if st.session_state.get("is_admin", False):
    menu = [
        "🍲 જમણવાર બુકિંગ",
        "🎁 સામાન્ય દાન (Donation)",
        "💸 ખર્ચની નોંધ (Expenses)",
        "📦 અનાજ & સ્ટોક (Inventory)",
        "📊 એડમિન & હિસાબ ડેશબોર્ડ",
    ]
elif st.session_state.get("is_operator", False):
    menu = [
        "🍲 જમણવાર બુકિંગ",
        "🎁 સામાન્ય દાન (Donation)",
        "💸 ખર્ચની નોંધ (Expenses)",
        "📦 અનાજ & સ્ટોક (Inventory)",
    ]
else:
    menu = [
        "🍲 જમણવાર બુકિંગ",
        "🎁 સામાન્ય દાન (Donation)",
    ]

choice = st.sidebar.radio("📌 મુખ્ય મેનૂ", menu)

# ==========================================
# ૧. જમણવાર બુકિંગ મોડ્યુલ
# ==========================================
if choice == "🍲 જમણવાર બુકિંગ":
    st.subheader("📅 જમણવાર ઓનલાઈન બુકિંગ")

    if st.session_state.get("is_admin", False):
        st.info(
            "🔓 એડમિન મોડ ચાલુ છે: તમે પાછલી (જૂની) તારીખ પણ પસંદ કરી શકો છો."
        )
        booking_date = st.date_input("૧. જમણવારની તારીખ પસંદ કરો *")
    else:
        booking_date = st.date_input(
            "૧. જમણવારની તારીખ પસંદ કરો *", min_value=date.today()
        )

    date_str = str(booking_date)

    cursor.execute(
        "SELECT meal_types FROM bookings WHERE booking_date = ?", (date_str,)
    )
    booked_records = cursor.fetchall()
    booked_meals = [
        m for row in booked_records if row[0] for m in row[0].split(", ")
    ]

    st.write("### ૨. ઉપલબ્ધ જમણવાર પસંદ કરો *")
    selected_meals = []

    col1, col2 = st.columns(2)
    cols = [col1, col2, col1, col2]

    for idx, meal in enumerate(ALL_MEALS):
        rate_display = int(MEAL_RATES[meal])
        label_text = f"{meal} (₹{rate_display})"

        if meal in booked_meals:
            cols[idx].error(f"❌ {meal} (બુક થયેલ છે)")
        else:
            if cols[idx].checkbox(label_text, key=f"chk_{meal}"):
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
                d_prefix = st.selectbox(
                    "પ્રીફિક્સ", prefix_options, key="p_donor"
                )
            with col_n1:
                raw_donor_name = st.text_input("૪. દાતાશ્રીનું નામ *")

            donor_name = (
                f"{d_prefix} {raw_donor_name.upper()}".strip()
                if raw_donor_name
                else ""
            )

            donor_phone = st.text_input(
                "૫. મોબાઈલ નંબર *", max_chars=10, placeholder="9876543210"
            )

        with c2:
            col_p2, col_n2 = st.columns([1, 2.5])
            with col_p2:
                s_prefix = st.selectbox(
                    "પ્રીફિક્સ", prefix_options, key="p_service"
                )
            with col_n2:
                raw_service_name = st.text_input(
                    "૬. જેમના નામે સેવા આપવી હોય તેમનું નામ *",
                    value=raw_donor_name,
                )

            service_for_name = (
                f"{s_prefix} {raw_service_name.upper()}".strip()
                if raw_service_name
                else ""
            )

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
                    f"📅 તારીખ: {date_str}%0A"
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
        st.info("💡 કૃપા કરીને ઉપર આપેલા બોક્સમાંથી ઓછામાં ઓછો ૧ જમણવાર પસંદ કરો.")

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

            d_name = (
                f"{don_prefix} {raw_d_name.upper()}".strip() if raw_d_name else ""
            )
            d_phone = st.text_input("મોબાઈલ નંબર", max_chars=10)
            d_type = st.selectbox(
                "દાનનો પ્રકાર",
                [
                    "સામાન્ય દાન (General)",
                    "વિકલાંગ સેવા દાન",
                    "અનાજ દાન",
                    "અન્ય",
                ],
            )
        with col2:
            d_amount = st.number_input("દાનની રકમ (₹) *", min_value=1.0)
            d_mode = st.selectbox(
                "પેમેન્ટ મોડ", ["Cash (રોકડ)", "Online (UPI / QR)", "Bank Transfer"]
            )
            d_utr = st.text_input(
                "UTR / Receipt No (ઓપ્શનલ)", placeholder="ઓપ્શનલ Ref ID"
            )

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
                    (
                        d_name,
                        d_phone,
                        d_type,
                        d_amount,
                        d_mode,
                        d_utr if d_utr else "N/A",
                    ),
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
            [
                "અનાજ / કરિયાણું / શાકભાજી",
                "વિકલાંગ સેવા સાધનો / મદદ",
                "રસોઈયા / સ્ટાફ પગાર",
                "ગેસ સિલિન્ડર / લાઈટ બિલ",
                "ટ્રાન્સપોર્ટ / ભાડું",
                "અન્ય પરચુરણ ખર્ચ",
            ],
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
                item_name = st.text_input(
                    "વસ્તુનું નામ *", placeholder="દા.ત. ઘઉં, ચોખા, સીંગતેલ"
                )
                t_type = st.radio(
                    "પ્રકાર *",
                    ["IN (આવક - દાન/ખરીદી)", "OUT (જાવક - રસોડામાં વપરાશ)"],
                )
                qty = st.number_input("જથ્થો *", min_value=0.1)
            with col2:
                unit = st.selectbox(
                    "એકમ (Unit)", ["કિલો (Kg)", "કટ્ટા/ગુણ", "ડબ્બા", "લિટર", "નંગ"]
                )
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
                        (
                            item_name.strip().upper(),
                            trans_code,
                            qty,
                            unit,
                            str(i_date),
                            remarks.upper(),
                        ),
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
                total_in = item_data[item_data["trans_type"] == "IN"][
                    "quantity"
                ].sum()
                total_out = item_data[item_data["trans_type"] == "OUT"][
                    "quantity"
                ].sum()
                balance = total_in - total_out
                unit_name = item_data["unit"].iloc[-1]

                summary.append(
                    {
                        "વસ્તુનું નામ": item,
                        "કુલ આવક (IN)": total_in,
                        "કુલ જાવક (OUT)": total_out,
                        "હાલનો સ્ટોક (Balance)": balance,
                        "એકમ": unit_name,
                    }
                )

            st.dataframe(pd.DataFrame(summary), use_container_width=True)
        else:
            st.info("હજુ સુધી કોઈ સ્ટોક એન્ટ્રી કરવામાં આવી નથી.")

# ==========================================
# ૫. એડમિન ડેશબોર્ડ (MASTER ADMIN ONLY)
# ==========================================
elif choice == "📊 એડમિન & હિસાબ ડેશબોર્ડ":
    st.subheader("🔒 માસ્ટર એડમિન પેનલ")

    c_jmn = cursor.execute(
        "SELECT SUM(amount) FROM bookings"
    ).fetchone()[0] or 0.0
    c_don = cursor.execute(
        "SELECT SUM(amount) FROM donations"
    ).fetchone()[0] or 0.0
    tot_inc = c_jmn + c_don

    tot_exp = cursor.execute(
        "SELECT SUM(amount) FROM expenses"
    ).fetchone()[0] or 0.0
    net_bal = tot_inc - tot_exp

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🍲 જમણવાર આવક", f"₹ {c_jmn:,.2f}")
    m2.metric("🎁 સામાન્ય દાન", f"₹ {c_don:,.2f}")
    m3.metric("📤 કુલ ખર્ચ", f"₹ {tot_exp:,.2f}")
    m4.metric("💵 હાથ પર બાકી (Net)", f"₹ {net_bal:,.2f}")

    st.markdown("---")
    st.write("### 📄 જૂની પાવતી / રસીદ જોઈને પ્રિન્ટ કરો")

    cursor.execute(
        "SELECT id, donor_name, booking_date FROM bookings ORDER BY id DESC"
    )
    all_bookings = cursor.fetchall()

    if all_bookings:
        booking_options = {
            f"રસીદ નં #{b[0]} - {b[1]} (તારીખ: {b[2]})": b[0] for b in all_bookings
        }
        selected_receipt_label = st.selectbox(
            "પ્રિન્ટ કરવા માટે જૂની રસીદ પસંદ કરો:",
            list(booking_options.keys()),
        )
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
    st.write("### 📋 જમણવાર બુકિંગ લિસ્ટ")
    df_b = pd.read_sql_query(
        "SELECT id, donor_name AS 'દાતાશ્રી', service_for_name AS 'જેમના નામે સેવા', phone AS 'મોબાઈલ', booking_date AS 'તારીખ', meal_types AS 'જમણવાર', meal_prep_type AS 'પ્રકાર', amount AS 'રકમ (₹)', payment_status AS 'Pay Status', payment_type AS 'Pay Type' FROM bookings ORDER BY id DESC",
        conn,
    )
    st.dataframe(df_b, use_container_width=True)

    st.markdown("---")
    st.write("### 📥 Excel રિપોર્ટ ડાઉનલોડ કરો")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.read_sql_query("SELECT * FROM bookings", conn).to_excel(
            writer, sheet_name="Jamanvar", index=False
        )
        pd.read_sql_query("SELECT * FROM donations", conn).to_excel(
            writer, sheet_name="Donations", index=False
        )
        pd.read_sql_query("SELECT * FROM expenses", conn).to_excel(
            writer, sheet_name="Expenses", index=False
        )
        pd.read_sql_query("SELECT * FROM inventory", conn).to_excel(
            writer, sheet_name="Inventory", index=False
        )

    st.download_button(
        label="📥 તમામ ડેટા Excel માં ડાઉનલોડ કરો",
        data=buffer.getvalue(),
        file_name="ngo_master_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
