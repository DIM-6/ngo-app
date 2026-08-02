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

# ==========================================
# NEW UPDATED CSS - HEADER FIXED
# ==========================================
st.markdown("""
<style>
/* Hide all icons using the most aggressive selector */
[data-testid="stIcon"] { display: none !important; }
button[data-testid="baseButton-secondary"] { display: none !important; }
svg { display: none !important; }
.stDateInput svg:not([data-testid="stIcon"]) { display: none !important; }
.stTextInput button { display: none !important; }
.stDateInput button { display: none !important; }

/* Main container */
.main .block-container {
    max-width: 680px !important;
    margin: 0 auto !important;
    padding-top: 0.8rem !important;
    padding-bottom: 2rem !important;
}

/* ===== NEW HEADER CSS START ===== */
.header-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 20px;
    border-top: 5px solid #F39C12;
    padding-top: 15px;
    margin-bottom: 5px;
}
.header-container .logo-img {
    height: 90px;
    width: auto;
}
.header-text-box {
    text-align: center;
    line-height: 1.2;
}
.h-title-green {
    color: #16A34A !important; 
    font-size: 24px !important; 
    font-weight: 900 !important; 
    margin: 0 !important;
    letter-spacing: 1px;
}
.h-title-blue {
    color: #0284C7 !important; 
    font-size: 20px !important; 
    font-weight: 800 !important; 
    margin: 0 !important;
}
.h-title-purple {
    color: #8E44AD !important; 
    font-size: 20px !important; 
    font-weight: 800 !important; 
    margin: 0 !important;
}
.h-reg {
    color: #4B5563 !important; 
    font-size: 12px !important; 
    font-weight: bold !important; 
    margin: 2px 0 0 0 !important;
}
.h-gujarati {
    color: #4B5563 !important;
    font-size: 13px !important;
    font-weight: bold !important;
    margin-top: 4px !important;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}
/* ===== NEW HEADER CSS END ===== */

/* Meal Cards */
.meal-card {
    border-radius: 10px;
    padding: 15px 10px;
    margin-bottom: 10px;
    text-align: center;
    min-height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.meal-card-available {
    background-color: #FFFFFF;
    border: 2px solid #D1D5DB;
}
.meal-card-selected {
    background-color: #EFF6FF;
    border: 3px solid #2563EB;
}
.meal-card-booked {
    background-color: #FEE2E2;
    border: 2px solid #EF4444;
    opacity: 0.6;
}

@media (max-width: 768px) {
    .main .block-container {
        max-width: 100% !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    .header-container {
        flex-direction: column !important;
        gap: 10px !important;
        padding-top: 10px !important;
    }
    .header-container .logo-img {
        height: 70px;
    }
    .h-title-green { font-size: 20px !important; }
    .h-title-blue, .h-title-purple { font-size: 17px !important; }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# NEW UPDATED HEADER (HTML)
# ==========================================
logo_b64_main = get_image_base64(LOGO_PATH)

if logo_b64_main:
    st.markdown(
        f"""
        <div class="header-container">
            <img src="data:image/png;base64,{logo_b64_main}" class="logo-img" />
            <div class="header-text-box">
                <p class="h-title-green">NARMADESHWAR</p>
                <p class="h-title-blue">VIKLANG VIKAAS</p>
                <p class="h-title-purple">MANAV SEVA TRUST</p>
                <p class="h-reg">Reg. No.: {NGO_REG_NO}</p>
                <div class="h-gujarati">
                    <span>જમણવાર બુકિંગ</span> | 
                    <span>દાન સ્વીકાર</span> | 
                    <span>ખર્ચ નોંધ</span> | 
                    <span>અનાજ સ્ટોક મેનેજમેન્ટ</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="header-container" style="flex-direction: column !important;">
            <div class="header-text-box">
                <p class="h-title-green">NARMADESHWAR</p>
                <p class="h-title-blue">VIKLANG VIKAAS</p>
                <p class="h-title-purple">MANAV SEVA TRUST</p>
                <p class="h-reg">Reg. No.: {NGO_REG_NO}</p>
                <div class="h-gujarati">
                    <span>જમણવાર બુકિંગ</span> | 
                    <span>દાન સ્વીકાર</span> | 
                    <span>ખર્ચ નોંધ</span> | 
                    <span>અનાજ સ્ટોક મેનેજમેન્ટ</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ==========================================
# LOGIN SYSTEM - SIMPLEST
# ==========================================
st.sidebar.markdown("### 🔑 સ્ટાફ / એડમિન લોગિન")

login_pwd = st.sidebar.text_input(
    "પાસવર્ડ",
    type="password",
    key="login_password",
    placeholder="••••••••"
)

st.sidebar.markdown("""
<style>
.stSidebar svg { display: none !important; }
.stSidebar button[data-testid="baseButton-secondary"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

if login_pwd == "ngo123":
    st.session_state["is_admin"] = True
    st.session_state["is_operator"] = True
    st.sidebar.success("✅ Admin Mode")
elif login_pwd == "op123":
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = True
    st.sidebar.success("✅ Operator Mode")
elif login_pwd != "":
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = False
    st.sidebar.error("❌ Wrong Password")
else:
    st.session_state["is_admin"] = False
    st.session_state["is_operator"] = False

st.sidebar.markdown("---")

# Menu
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
# ૧. જમણવાર બુકિંગ
# ==========================================
if choice == "🍲 જમણવાર બુકિંગ":
    st.subheader("📅 જમણવાર ઓનલાઈન બુકિંગ")

    if st.session_state.get("is_admin", False):
        st.info("🔓 એડમિન મોડ: જૂની તારીખ પણ પસંદ કરી શકો છો.")
        booking_date = st.date_input("૧. જમણવારની તારીખ પસંદ કરો")
    else:
        booking_date = st.date_input("૧. જમણવારની તારીખ પસંદ કરો", min_value=date.today())

    date_str = str(booking_date)

    cursor.execute("SELECT meal_types FROM bookings WHERE booking_date = ?", (date_str,))
    booked_records = cursor.fetchall()
    booked_meals = []
    for row in booked_records:
        if row[0]:
            for m in row[0].split(", "):
                if m.strip():
                    booked_meals.append(m.strip())

    st.write("### ૨. ઉપલબ્ધ જમણવાર પસંદ કરો (કાર્ડ પર ક્લિક કરો)")

    if "selected_meals_list" not in st.session_state:
        st.session_state["selected_meals_list"] = []

    # Display meal cards
    col1, col2 = st.columns(2)

    for idx, meal in enumerate(ALL_MEALS):
        rate_display = int(MEAL_RATES[meal])
        is_booked = meal in booked_meals

        with col1 if idx % 2 == 0 else col2:
            if is_booked:
                st.markdown(
                    f"""
                    <div class="meal-card meal-card-booked">
                        <div style="color: #991B1B; font-weight: 700;">❌ {meal}</div>
                        <div style="color: #B91C1C; font-weight: 800;">₹{rate_display}</div>
                        <div style="color: #991B1B; font-size: 12px;">✖ બુક થયેલ</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                is_selected = meal in st.session_state["selected_meals_list"]
                card_class = "meal-card meal-card-selected" if is_selected else "meal-card meal-card-available"
                status = "✅ સિલેક્ટ થયેલ" if is_selected else "🖱️ સિલેક્ટ કરો"
                
                if st.button(
                    f"{meal}\n₹{rate_display}\n{status}",
                    key=f"meal_{idx}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    if is_selected:
                        st.session_state["selected_meals_list"].remove(meal)
                    else:
                        st.session_state["selected_meals_list"].append(meal)
                    st.rerun()

    selected_meals = []
    for meal in ALL_MEALS:
        if meal in st.session_state["selected_meals_list"] and meal not in booked_meals:
            selected_meals.append(meal)

    st.markdown("---")

    if selected_meals:
        st.success(f"✅ સિલેક્ટ થયેલ: {', '.join(selected_meals)}")
        st.write(f"💰 કુલ: ₹{sum(MEAL_RATES[m] for m in selected_meals):,.2f}")
        
        st.markdown("---")
        
        meal_prep_type = st.radio(
            "૩. પ્રકાર",
            ["૧. સંસ્થામાં બનાવવાનું", "૨. તૈયાર લાવશે"],
        )

        prefix_options = ["શ્રી", "સ્વ.", "ગં.સ્વ.", "શ્રીમતી", "કુ."]

        c1, c2 = st.columns(2)
        with c1:
            col_p1, col_n1 = st.columns([1, 2.5])
            with col_p1:
                d_prefix = st.selectbox("પ્રીફિક્સ", prefix_options, key="p_donor")
            with col_n1:
                raw_donor_name = st.text_input("૪. દાતાશ્રીનું નામ")

            donor_name = f"{d_prefix} {raw_donor_name.upper()}".strip() if raw_donor_name else ""
            donor_phone = st.text_input("૫. મોબાઈલ", max_chars=10, placeholder="9876543210")

        with c2:
            col_p2, col_n2 = st.columns([1, 2.5])
            with col_p2:
                s_prefix = st.selectbox("પ્રીફિક્સ", prefix_options, key="p_service")
            with col_n2:
                raw_service_name = st.text_input("૬. સેવા નામ", value=raw_donor_name)
            service_for_name = f"{s_prefix} {raw_service_name.upper()}".strip() if raw_service_name else ""

        payment_status = "N/A"
        payment_type = "N/A"
        utr_number = "N/A"
        final_amount = 0.0

        if meal_prep_type == "૧. સંસ્થામાં બનાવવાનું":
            st.markdown("---")
            st.write("### 💳 પેમેન્ટ")

            p_col1, p_col2 = st.columns(2)
            with p_col1:
                payment_status = st.radio("Payment આવી ગયેલ?", ["Yes", "No"], horizontal=True)
                payment_type = st.selectbox("Payment Type", ["Cash", "Online", "Bank Transfer"])
            with p_col2:
                final_amount = st.number_input("રકમ (₹)", value=sum(MEAL_RATES[m] for m in selected_meals), step=50.0)
                if payment_type in ["Online", "Bank Transfer"]:
                    utr_number = st.text_input("UTR/Ref No", placeholder="12 અંકનો ID")
                    if not utr_number:
                        utr_number = "Not Provided"

        if st.button("💾 બુકિંગ સેવ કરો", type="primary"):
            if not raw_donor_name or not donor_phone:
                st.error("❌ દાતાનું નામ અને મોબાઈલ ભરો.")
            else:
                meals_str = ", ".join(selected_meals)
                cursor.execute(
                    """
                    INSERT INTO bookings (donor_name, phone, service_for_name, booking_date, meal_types, meal_prep_type, amount, payment_status, payment_type, utr_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (donor_name, donor_phone, service_for_name, date_str, meals_str, meal_prep_type, final_amount, payment_status, payment_type, utr_number),
                )
                conn.commit()
                st.success("✅ બુકિંગ સેવ થઈ ગયું!")
                st.session_state["selected_meals_list"] = []
                st.rerun()
    else:
        st.info("💡 જમણવાર પસંદ કરો.")

# ==========================================
# ૨. દાન
# ==========================================
elif choice == "🎁 સામાન્ય દાન (Donation)":
    st.subheader("🎁 સામાન્ય દાન")

    prefix_options = ["શ્રી", "સ્વ.", "ગં.સ્વ.", "શ્રીમતી", "કુ."]

    with st.form("donation_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            c_dp, c_dn = st.columns([1, 2.5])
            with c_dp:
                don_prefix = st.selectbox("પ્રીફિક્સ", prefix_options)
            with c_dn:
                raw_d_name = st.text_input("દાતાનું નામ")
            d_name = f"{don_prefix} {raw_d_name.upper()}".strip() if raw_d_name else ""
            d_phone = st.text_input("મોબાઈલ", max_chars=10)
            d_type = st.selectbox("દાન પ્રકાર", ["સામાન્ય", "વિકલાંગ સેવા", "અનાજ", "અન્ય"])
        with col2:
            d_amount = st.number_input("રકમ (₹)", min_value=1.0)
            d_mode = st.selectbox("પેમેન્ટ", ["Cash", "Online", "Bank Transfer"])
            d_utr = st.text_input("UTR (ઓપ્શનલ)")
        if st.form_submit_button("💾 દાન સેવ કરો"):
            if not raw_d_name or d_amount <= 0:
                st.error("❌ દાતાનું નામ અને રકમ ભરો.")
            else:
                cursor.execute("INSERT INTO donations (donor_name, phone, donation_type, amount, payment_mode, utr_number) VALUES (?, ?, ?, ?, ?, ?)", (d_name, d_phone, d_type, d_amount, d_mode, d_utr if d_utr else "N/A"))
                conn.commit()
                st.success(f"✅ ₹{d_amount} દાન સેવ થયું!")

# ==========================================
# ૩. ખર્ચ
# ==========================================
elif choice == "💸 ખર્ચની નોંધ (Expenses)":
    st.subheader("💸 ખર્ચ")

    with st.form("expense_form", clear_on_submit=True):
        e_date = st.date_input("તારીખ")
        e_cat = st.selectbox("પ્રકાર", ["અનાજ/કરિયાણું", "વિકલાંગ સેવા", "સ્ટાફ પગાર", "ગેસ/લાઈટ", "ટ્રાન્સપોર્ટ", "અન્ય"])
        e_desc = st.text_input("વિગત")
        e_amount = st.number_input("રકમ (₹)", min_value=1.0)
        if st.form_submit_button("💾 ખર્ચ સેવ કરો"):
            if not e_desc or e_amount <= 0:
                st.error("❌ વિગત અને રકમ ભરો.")
            else:
                cursor.execute("INSERT INTO expenses (expense_date, category, description, amount) VALUES (?, ?, ?, ?)", (str(e_date), e_cat, e_desc.upper(), e_amount))
                conn.commit()
                st.success("✅ ખર્ચ સેવ થયો!")

# ==========================================
# ૪. સ્ટોક
# ==========================================
elif choice == "📦 અનાજ & સ્ટોક (Inventory)":
    st.subheader("📦 સ્ટોક")

    tab1, tab2 = st.tabs(["➕ નવી એન્ટ્રી", "📊 સ્ટોક સ્ટેટસ"])

    with tab1:
        with st.form("stock_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                item_name = st.text_input("વસ્તુનું નામ")
                t_type = st.radio("પ્રકાર", ["IN (આવક)", "OUT (જાવક)"])
                qty = st.number_input("જથ્થો", min_value=0.1)
            with col2:
                unit = st.selectbox("એકમ", ["કિલો", "ગ્રામ", "લિટર", "નંગ"])
                i_date = st.date_input("તારીખ")
                remarks = st.text_input("નોંધ")
            if st.form_submit_button("💾 સ્ટોક સેવ કરો"):
                if not item_name or qty <= 0:
                    st.error("❌ વસ્તુ અને જથ્થો ભરો.")
                else:
                    code = "IN" if "IN" in t_type else "OUT"
                    cursor.execute("INSERT INTO inventory (item_name, trans_type, quantity, unit, entry_date, remarks) VALUES (?, ?, ?, ?, ?, ?)", (item_name.upper(), code, qty, unit, str(i_date), remarks.upper()))
                    conn.commit()
                    st.success("✅ સ્ટોક એન્ટ્રી થઈ!")

    with tab2:
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        if not df_inv.empty:
            summary = []
            for item in df_inv["item_name"].unique():
                item_data = df_inv[df_inv["item_name"] == item]
                total_in = item_data[item_data["trans_type"] == "IN"]["quantity"].sum()
                total_out = item_data[item_data["trans_type"] == "OUT"]["quantity"].sum()
                summary.append({"વસ્તુ": item, "IN": total_in, "OUT": total_out, "Balance": total_in - total_out, "Unit": item_data["unit"].iloc[-1]})
            st.dataframe(pd.DataFrame(summary), use_container_width=True)
        else:
            st.info("કોઈ સ્ટોક નથી.")

# ==========================================
# ૫. ડેશબોર્ડ
# ==========================================
elif choice == "📊 એડમિન & હિસાબ ડેશબોર્ડ":
    st.subheader("📊 ડેશબોર્ડ")

    c_jmn = cursor.execute("SELECT SUM(amount) FROM bookings").fetchone()[0] or 0.0
    c_don = cursor.execute("SELECT SUM(amount) FROM donations").fetchone()[0] or 0.0
    tot_exp = cursor.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🍲 જમણવાર", f"₹{c_jmn:,.2f}")
    m2.metric("🎁 દાન", f"₹{c_don:,.2f}")
    m3.metric("💸 ખર્ચ", f"₹{tot_exp:,.2f}")
    m4.metric("💵 બાકી", f"₹{(c_jmn + c_don - tot_exp):,.2f}")

    st.markdown("---")
    st.write("### 📋 બુકિંગ લિસ્ટ")
    df_b = pd.read_sql_query("SELECT id, donor_name, phone, booking_date, meal_types, amount FROM bookings ORDER BY id DESC", conn)
    st.dataframe(df_b, use_container_width=True)

    st.markdown("---")
    st.write("### 📥 Excel ડાઉનલોડ")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.read_sql_query("SELECT * FROM bookings", conn).to_excel(writer, sheet_name="Bookings", index=False)
        pd.read_sql_query("SELECT * FROM donations", conn).to_excel(writer, sheet_name="Donations", index=False)
        pd.read_sql_query("SELECT * FROM expenses", conn).to_excel(writer, sheet_name="Expenses", index=False)
        pd.read_sql_query("SELECT * FROM inventory", conn).to_excel(writer, sheet_name="Inventory", index=False)
    st.download_button("📥 ડાઉનલોડ કરો", data=buffer.getvalue(), file_name="ngo_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ==========================================
# PDF Functions (kept for compatibility)
# ==========================================
def auto_save_pdf_to_folder(booking_info):
    try:
        clean_donor_name = "".join(c for c in booking_info["donor_name"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
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
        c.drawString(10, height - 66, f"Receipt No: #{booking_info.get('id', 'N/A')}")
        c.drawString(width - 80, height - 66, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
        c.line(10, height - 70, width - 10, height - 70)
        y = height - 85
        details = [
            ("Donor:", str(booking_info["donor_name"]).upper()),
            ("Phone:", str(booking_info["phone"])),
            ("Service For:", str(booking_info["service_for_name"]).upper()),
            ("Meal Date:", str(booking_info["booking_date"])),
            ("Meals:", str(booking_info["meal_types"])),
            ("Prep:", str(booking_info["meal_prep_type"])),
            ("Amount:", f"Rs. {booking_info['amount']:,.2f}"),
            ("Mode:", f"{booking_info['payment_type']} ({booking_info['payment_status']})"),
        ]
        for label, val in details:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(12, y, label)
            c.setFont("Helvetica", 8)
            c.drawString(75, y, val[:25])
            y -= 13
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColorRGB(0.02, 0.59, 0.41)
        c.drawCentredString(width / 2, 12, "Thank you for your noble support!")
        c.save()
        return file_path
    except Exception as e:
        return None

def render_html_receipt(booking_info):
    logo_b64 = get_image_base64(LOGO_PATH)
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="receipt-logo" />' if logo_b64 else ""
    clean_donor = "".join(c for c in booking_info["donor_name"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_").upper()
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
            body {{ font-family: 'Noto Sans Gujarati', Arial, sans-serif; background: #ffffff; margin: 0; padding: 4px; display: flex; justify-content: center; }}
            .receipt-box {{ width: 100%; max-width: 380px; background: #ffffff; border: 1.5px solid #1e3a8a; border-radius: 8px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header-flex {{ display: flex; align-items: center; justify-content: center; gap: 10px; border-bottom: 1.5px solid #1e3a8a; padding-bottom: 6px; margin-bottom: 8px; }}
            .receipt-logo {{ height: 60px; width: auto; }}
            .title-box {{ text-align: left; display: flex; flex-direction: column; justify-content: center; line-height: 1.1; }}
            .title-l1 {{ color: #16A34A; font-size: 14px; font-weight: 900; }}
            .title-l2 {{ color: #0284C7; font-size: 12px; font-weight: 800; }}
            .title-l3 {{ color: #1E3A8A; font-size: 12px; font-weight: 800; }}
            .reg-no {{ color: #4b5563; font-size: 9px; font-weight: 700; margin-top: 2px; }}
            .receipt-nametag {{ color: #1d4ed8; margin-top: 1px; font-size: 11px; font-weight: 700; }}
            .row {{ display: flex; justify-content: space-between; padding: 4px 6px; border-bottom: 1px solid #e2e8f0; font-size: 11px; gap: 6px; }}
            .row:nth-child(even) {{ background-color: #f8fafc; }}
            .label {{ font-weight: 600; color: #1e3a8a; flex-shrink: 0; }}
            .value {{ color: #111827; text-align: right; font-weight: 500; text-transform: uppercase; }}
            .total-row {{ background-color: #eff6ff !important; font-weight: 700; color: #1e3a8a; font-size: 12px; border-top: 1px solid #1e3a8a; border-bottom: 1px solid #1e3a8a; }}
            .footer {{ text-align: center; margin-top: 8px; color: #059669; font-weight: 600; font-size: 10px; line-height: 1.3; }}
            .print-button {{ display: block; width: 100%; background-color: #1e3a8a; color: white; text-align: center; padding: 8px; margin-top: 10px; border: none; border-radius: 5px; font-size: 13px; font-weight: bold; cursor: pointer; }}
            @media print {{ @page {{ size: A6 portrait; margin: 0; }} .print-button {{ display: none; }} body {{ padding: 0; margin: 0; }} .receipt-box {{ border: 1px solid #000; box-shadow: none; border-radius: 0; }} }}
        </style>
        <script>
            function printReceipt() {{
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
            <div class="row"><span class="label">પાવતી નં:</span><span class="value">#{booking_info.get('id', 'N/A')}</span></div>
            <div class="row"><span class="label">તારીખ:</span><span class="value">{datetime.now().strftime('%d-%m-%Y')}</span></div>
            <div class="row"><span class="label">દાતાશ્રી:</span><span class="value">{booking_info['donor_name']}</span></div>
            <div class="row"><span class="label">મોબાઈલ:</span><span class="value">{booking_info['phone']}</span></div>
            <div class="row"><span class="label">સેવા નામ:</span><span class="value">{booking_info['service_for_name']}</span></div>
            <div class="row"><span class="label">જમણવાર તારીખ:</span><span class="value">{booking_info['booking_date']}</span></div>
            <div class="row"><span class="label">જમણવાર:</span><span class="value">{booking_info['meal_types']}</span></div>
            <div class="row"><span class="label">પ્રકાર:</span><span class="value">{booking_info['meal_prep_type']}</span></div>
            <div class="row total-row"><span>રકમ:</span><span>₹ {booking_info['amount']:,.2f}</span></div>
            <div class="row"><span class="label">પેમેન્ટ:</span><span class="value">{booking_info['payment_type']} ({booking_info['payment_status']})</span></div>
            <div class="footer">Thank you for your noble support!<br>આપના માનવસેવા યોગદાન બદલ આભાર!</div>
            <button class="print-button" onclick="printReceipt()">🖨️ પાવતી પ્રિન્ટ કરો / PDF સેવ કરો</button>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=530, scrolling=True)
