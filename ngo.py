import base64
from datetime import date, datetime, timedelta
import io
import os
import pandas as pd
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas

# ==========================================
# ⚙️ FORCE LIGHT MODE CONFIG (FIXES BLACK BACKGROUND ON ANDROID/WINDOWS)
# ==========================================
try:
    os.makedirs(".streamlit", exist_ok=True)
    config_path = os.path.join(".streamlit", "config.toml")
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write(
                "[theme]\nbase=\"light\"\nprimaryColor=\"#059669\"\nbackgroundColor=\"#FFFFFF\"\nsecondaryBackgroundColor=\"#F3F4F6\"\ntextColor=\"#111827\"\nfont=\"sans serif\"\n"
            )
except Exception:
    pass

# ==========================================
# 🗄️ SUPABASE DATABASE SETUP
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("⚠️ Supabase સાથે કનેક્શન થઈ શક્યું નથી. કૃપા કરીને Streamlit Secrets માં SUPABASE_URL અને SUPABASE_KEY ચેક કરો.")
    st.stop()

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
        "rg_ngo_logo.jpg",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            LOGO_PATH = p
            break

BASE_DIR = os.getcwd()
RECEIPTS_DIR = os.path.join(BASE_DIR, "Receipts_Images")
LETTERS_DIR = os.path.join(BASE_DIR, "Letters")
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

# ૩ કેટેગરી અને ભાવ
MEAL_RATES = {
    (
        "૧. આખા દિવસનો જમણવાર (સવારનો ચા-નાસ્તો, બપોરનું મિષ્ટાન્ન ભોજન, સાંજનો"
        " નાસ્તો, રાત્રિનું સાદું ભોજન)"
    ): 4000.0,
    "૨. સવારનો ચા-નાસ્તો અને બપોરનું મિષ્ટાન્ન ભોજન": 2500.0,
    "૩. સાંજનો નાસ્તો અને રાત્રિનું મિષ્ટાન્ન ભોજન": 2500.0,
}

ALL_MEALS = list(MEAL_RATES.keys())

st.set_page_config(
    page_title="NARMADESHWAR VIKLANG VIKAAS MANAV SEVA TRUST",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- તમારો જૂનો CSS કોડ (કોઈ ફેરફાર નહીં) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;600;700;800;900&display=swap');
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    label, p, span, div, h1, h2, h3, h4, .stMarkdown { font-family: 'Noto Sans Gujarati', sans-serif !important; color: #111827 !important; }
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span { color: #111827 !important; font-weight: 700 !important; font-size: 14px !important; }
    input[type="text"], input[type="password"], input[type="number"] { text-transform: uppercase !important; background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB !important; border-radius: 6px !important; }
    [data-testid="stSidebar"] { display: none !important; }
    footer, #MainMenu { display: none !important; }
    [data-testid="stFormSubmitButton"] > button, [data-testid="stDownloadButton"] > button { border-radius: 6px !important; padding: 4px 14px !important; font-size: 12px !important; font-weight: 700 !important; min-height: 34px !important; height: 34px !important; background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important; color: #FFFFFF !important; border: 1px solid #047857 !important; }
    div.row-widget.stButton > button[kind="secondary"], button[data-testid="baseButton-secondary"] { background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%) !important; border: 2px solid #10B981 !important; color: #065F46 !important; font-weight: 700 !important; text-align: center !important; padding: 12px 16px !important; border-radius: 8px !important; margin-bottom: 8px !important; width: 100% !important; }
    div.row-widget.stButton > button[kind="primary"], button[data-testid="baseButton-primary"] { background: linear-gradient(135deg, #059669 0%, #047857 100%) !important; border: 2px solid #064E3B !important; color: #FFFFFF !important; font-weight: 700 !important; text-align: center !important; padding: 12px 16px !important; border-radius: 8px !important; margin-bottom: 8px !important; width: 100% !important; }
    .main .block-container { max-width: 900px !important; margin: 0 auto !important; padding-top: 0.8rem !important; padding-bottom: 2rem !important; }
    .header-wrapper { display: flex; align-items: center; gap: 25px; margin-bottom: 5px; border-top: 5px solid #F39C12; padding-top: 15px; width: 75% !important; margin-left: auto !important; margin-right: auto !important; }
    .header-wrapper img { height: 120px !important; width: auto; object-fit: contain; }
    .header-text-box { display: flex; flex-direction: column; justify-content: center; text-align: left; line-height: 1.35; }
    .h-title-1 { color: #16A34A !important; font-size: 24px !important; font-weight: 900 !important; margin: 0 !important; letter-spacing: 5px !important; }
    .h-title-2 { color: #0284C7 !important; font-size: 18px !important; font-weight: 800 !important; margin: 0 !important; letter-spacing: 4px !important; }
    .h-title-3 { color: #1E3A8A !important; font-size: 18px !important; font-weight: 800 !important; margin: 0 !important; letter-spacing: 4px !important; }
    .h-reg { color: #4B5563 !important; font-size: 11px !important; font-weight: bold !important; margin: 5px 0 0 0 !important; }
    @media (max-width: 768px) { .header-wrapper { width: 100% !important; flex-direction: column !important; text-align: center !important; } }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 🖼️ AUTO-SAVE BACKEND IMAGE & PRINTABLE HTML FUNCTIONS (SAME AS OLD)
# ==========================================
def auto_save_image_to_folder(booking_info):
    try:
        from PIL import ImageDraw, ImageFont
        clean_donor_name = "".join(c for c in booking_info["donor_name"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"Receipt_No_{booking_info.get('id', 'N/A')}_{clean_donor_name}.png"
        file_path = os.path.join(RECEIPTS_DIR, filename)
        img_width, img_height = 800, 1150
        image = Image.new("RGB", (img_width, img_height), color="white")
        draw = ImageDraw.Draw(image)
        draw.rectangle([15, 15, img_width - 15, img_height - 15], outline="#1e3a8a", width=4)
        font_path = "GujaratiFont.ttf"
        try:
            font_large = ImageFont.truetype(font_path, 28) if os.path.exists(font_path) else ImageFont.load_default()
            font_med = ImageFont.truetype(font_path, 22) if os.path.exists(font_path) else ImageFont.load_default()
            font_small = ImageFont.truetype(font_path, 20) if os.path.exists(font_path) else ImageFont.load_default()
        except:
            font_large = font_med = font_small = ImageFont.load_default()

        draw.text((40, 40), NGO_NAME, fill="#16A34A", font=font_large)
        draw.text((40, 85), f"Reg. No: {NGO_REG_NO}", fill="#4b5563", font=font_small)
        draw.line([40, 130, img_width - 40, 130], fill="#1e3a8a", width=2)
        y = 160
        details = [
            ("પાવતી નં:", f"#{booking_info.get('id', 'N/A')}"),
            ("તારીખ:", datetime.now().strftime("%d-%m-%Y")),
            ("દાતાશ્રી:", str(booking_info["donor_name"])),
            ("મોબાઈલ:", str(booking_info["phone"])),
            ("સેવા નામ:", str(booking_info["service_for_name"])),
            ("જમણવાર તારીખ:", fmt_date(booking_info["booking_date"])),
            ("નિમિત્ત:", str(booking_info.get("occasion", "N/A"))),
            ("જમણવાર:", str(booking_info["meal_types"])),
            ("પ્રકાર:", str(booking_info["meal_prep_type"])),
            ("રકમ:", f"Rs. {booking_info['amount']:,.2f}"),
            ("પેમેન્ટ:", f"{booking_info['payment_type']} ({booking_info['payment_status']})"),
        ]
        for label, val in details:
            draw.text((50, y), label, fill="#1e3a8a", font=font_med)
            draw.text((320, y), val, fill="#111827", font=font_small)
            y += 48
        image.save(file_path)
        return file_path
    except Exception as e:
        return None

def render_html_receipt(booking_info):
    logo_b64 = get_image_base64(LOGO_PATH)
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="receipt-logo" />' if logo_b64 else ""
    html_code = f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    body {{ font-family: sans-serif; padding:4px; display:flex; justify-content:center; }}
    .receipt-box {{ width:100%; max-width:380px; border: 1.5px solid #1e3a8a; padding:10px; border-radius:8px; }}
    .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 4px; font-size: 11px; }}
    .label {{ font-weight:bold; color: #1e3a8a; }}
    .print-btn {{ width: 100%; background: #1e3a8a; color: white; padding: 6px; border-radius: 5px; cursor: pointer; }}
    </style></head><body>
    <div class="receipt-box">
        <h4>NARMADESHWAR VIKLANG VIKAAS MANAV SEVA TRUST</h4>
        <div class="row"><span class="label">પાવતી નં:</span><span>#{booking_info.get('id', 'N/A')}</span></div>
        <div class="row"><span class="label">દાતાશ્રી:</span><span>{booking_info['donor_name']}</span></div>
        <div class="row"><span class="label">મોબાઈલ:</span><span>{booking_info['phone']}</span></div>
        <div class="row"><span class="label">જમણવાર તારીખ:</span><span>{fmt_date(booking_info['booking_date'])}</span></div>
        <div class="row"><span class="label">જમણવાર:</span><span>{booking_info['meal_types']}</span></div>
        <div class="row"><span class="label">રકમ:</span><span>₹ {booking_info['amount']}</span></div>
        <button class="print-btn" onclick="window.print()">🖨️ પાવતી પ્રિન્ટ કરો</button>
    </div></body></html>
    """
    components.html(html_code, height=500, scrolling=True)


def render_html_letter(letter_info):
    html_code = f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    body {{ font-family: sans-serif; padding:20px; }}
    .letter-box {{ border: 2px solid #1e3a8a; padding: 20px; }}
    </style></head><body>
    <div class="letter-box">
        <h3 style="color:#16A34A; text-align:center;">NARMADESHWAR VIKLANG VIKAAS MANAV SEVA TRUST</h3>
        <p><b>જાવક નં:</b> {letter_info.get('outward_no')} | <b>તારીખ:</b> {fmt_date(letter_info.get('letter_date'))}</p>
        <p><b>પ્રતિ,</b><br>{letter_info.get('recipient')}</p>
        <p><b>વિષય:</b> {letter_info.get('subject')}</p>
        <p>{letter_info.get('body_text')}</p>
        <button onclick="window.print()">🖨️ પ્રિન્ટ કરો</button>
    </div></body></html>
    """
    components.html(html_code, height=600, scrolling=True)


# ==========================================
# 🎯 HEADER & LOGIN DESIGN
# ==========================================
logo_b64_main = get_image_base64(LOGO_PATH)
if logo_b64_main:
    st.markdown(f'<div class="header-wrapper"><img src="data:image/png;base64,{logo_b64_main}" /><div class="header-text-box"><p class="h-title-1">NARMADESHWAR</p><p class="h-title-2">VIKLANG VIKAAS</p><p class="h-title-3">MANAV SEVA TRUST</p></div></div>', unsafe_allow_html=True)

st.markdown("### 🔑 સ્ટાફ / એડમિન લોગિન")
if not st.session_state.get("is_admin", False) and not st.session_state.get("is_operator", False):
    login_pwd = st.text_input("પાસવર્ડ દાખલ કરો", type="password")
    if login_pwd == "ngo123":
        st.session_state["is_admin"] = True; st.session_state["is_operator"] = True; st.rerun()
    elif login_pwd == "op123":
        st.session_state["is_admin"] = False; st.session_state["is_operator"] = True; st.rerun()
else:
    st.success("🔓 લોગિન સફળ!")
    if st.button("🚪 લોગ આઉટ (Logout)"):
        st.session_state["is_admin"] = False; st.session_state["is_operator"] = False; st.rerun()

is_admin = st.session_state.get("is_admin", False)
is_operator = st.session_state.get("is_operator", False)

if is_admin or is_operator:
    tabs = st.tabs(["🍲 જમણવાર", "🎁 દાન", "💸 ખર્ચ", "📦 સ્ટોક", "📜 લેટર", "📊 ડેશબોર્ડ"])
    t_booking, t_donation, t_expense, t_inventory, t_letter, t_dashboard = tabs
else:
    selected_menu = st.selectbox("મેનુ પસંદ કરો", ["🍲 જમણવાર બુકિંગ", "🎁 સામાન્ય દાન (Donation)"], index=None)
    t_booking, t_donation, t_expense, t_inventory, t_letter, t_dashboard = None, None, None, None, None, None
    if selected_menu == "🍲 જમણવાર બુકિંગ": t_booking = st.container()
    elif selected_menu == "🎁 સામાન્ય દાન (Donation)": t_donation = st.container()

# ==========================================
# ૧. જમણવાર બુકિંગ મોડ્યુલ (Supabase Integration)
# ==========================================
def render_booking_module():
    st.subheader("📅 જમણવાર ઓનલાઈન બુકિંગ")
    booking_date = st.date_input("૧. જમણવારની તારીખ પસંદ કરો", key="b_date")
    date_str = str(booking_date)

    # Supabase માંથી તારીખ મુજબ બુક થયેલા જમણવાર ખેંચો
    res = supabase.table("bookings").select("meal_types").eq("booking_date", date_str).execute()
    booked_records = res.data
    booked_meals = []
    
    for row in booked_records:
        val = row.get("meal_types", "").strip()
        if val == ALL_MEALS[0]:
            if ALL_MEALS[0] not in booked_meals: booked_meals.append(ALL_MEALS[0])
        else:
            for m in val.split(", "):
                if m not in booked_meals: booked_meals.append(m)

    meal_prep_type = st.radio("૨. જમણવારનો પ્રકાર", ["૧. સંસ્થામાં બનાવવાનું છે", "૨. તૈયાર બનાવીને લાવશે"])
    is_brought_ready = meal_prep_type == "૨. તૈયાર બનાવીને લાવશે"

    if "selected_meals_list" not in st.session_state: st.session_state["selected_meals_list"] = []
    current_list = st.session_state["selected_meals_list"]

    for c_idx, meal in enumerate(ALL_MEALS):
        is_booked = meal in booked_meals
        if st.button(f"{meal} - {'(Booked)' if is_booked else 'Select'}", disabled=is_booked, key=f"btn_{c_idx}"):
            if meal in current_list: current_list.remove(meal)
            else: current_list.append(meal)
            st.session_state["selected_meals_list"] = current_list
            st.rerun()

    selected_meals = [m for m in current_list if m not in booked_meals]

    if selected_meals:
        raw_donor_name = st.text_input("દાતાશ્રીનું નામ *")
        donor_phone = st.text_input("મોબાઈલ નંબર *")
        service_for_name = st.text_input("સેવા માટે નામ")
        meal_occasion = st.selectbox("નિમિત્ત *", ["જન્મદિન", "પુણ્યતિથિ", "અન્ય"])
        final_amount = st.number_input("રકમ (₹) *", value=sum(MEAL_RATES[m] for m in selected_meals) if not is_brought_ready else 500.0)
        payment_status = st.radio("પેમેન્ટ", ["Yes (આવી ગયેલ છે)", "No (બાકી છે)"], horizontal=True)
        payment_type = st.selectbox("પેમેન્ટ મોડ", ["Cash (રોકડ)", "Online (UPI / QR)", "Bank Transfer"])

        if st.button("💾 બુકિંગ સેવ કરો", type="primary"):
            if not raw_donor_name or not donor_phone:
                st.error("❌ દાતાનું નામ અને નંબર ફરજિયાત છે.")
            else:
                data = {
                    "donor_name": raw_donor_name.upper(),
                    "phone": donor_phone,
                    "service_for_name": service_for_name.upper(),
                    "booking_date": date_str,
                    "meal_types": ", ".join(selected_meals),
                    "meal_prep_type": meal_prep_type,
                    "occasion": meal_occasion.upper(),
                    "amount": final_amount,
                    "payment_status": payment_status,
                    "payment_type": payment_type,
                    "utr_number": "N/A"
                }
                
                # Supabase Insert
                response = supabase.table("bookings").insert(data).execute()
                last_id = response.data[0]['id'] # નવો ID મેળવવો

                st.success("🎉 બુકિંગ સફળતાપૂર્વક સેવ થઈ ગયું છે!")
                st.session_state["selected_meals_list"] = []
                data["id"] = last_id
                render_html_receipt(data)

# ==========================================
# ૨. દાન (Donations - Supabase)
# ==========================================
def render_donation_module():
    st.subheader("🎁 સામાન્ય દાન સ્વીકાર")
    with st.form("donation_form", clear_on_submit=True):
        d_name = st.text_input("દાતાનું પૂરૂં નામ *")
        d_phone = st.text_input("મોબાઈલ નંબર")
        d_type = st.selectbox("પ્રકાર", ["સામાન્ય દાન", "વિકલાંગ સેવા દાન", "અનાજ દાન", "અન્ય"])
        d_amount = st.number_input("રકમ (₹) *", min_value=1.0)
        
        if st.form_submit_button("💾 દાન સેવ કરો"):
            data = {
                "donor_name": d_name.upper(),
                "phone": d_phone,
                "donation_type": d_type,
                "amount": d_amount,
                "payment_mode": "Cash",
                "utr_number": "N/A"
            }
            supabase.table("donations").insert(data).execute()
            st.success("✅ દાન નોંધાઈ ગયું છે.")

# ==========================================
# 3. ખર્ચ (Expenses - Supabase)
# ==========================================
def render_expense_module():
    st.write("#### 💸 NGO રોજિંદો ખર્ચ")
    with st.form("expense_form", clear_on_submit=True):
        e_date = st.date_input("ખર્ચની તારીખ")
        e_cat = st.selectbox("ખર્ચનો પ્રકાર", ["કરિયાણું", "પગાર", "લાઈટ બિલ", "અન્ય"])
        e_desc = st.text_input("વિગત")
        e_amount = st.number_input("રકમ (₹)", min_value=1.0)
        
        if st.form_submit_button("💾 સેવ કરો"):
            data = {"expense_date": str(e_date), "category": e_cat, "description": e_desc.upper(), "amount": e_amount}
            supabase.table("expenses").insert(data).execute()
            st.success("✅ ખર્ચ નોંધાઈ ગયો.")

# ==========================================
# 4. સ્ટોક (Inventory - Supabase)
# ==========================================
def render_inventory_module():
    st.write("#### 📦 અનાજ સ્ટોક")
    with st.form("stock_form"):
        item_name = st.text_input("વસ્તુનું નામ")
        t_type = st.radio("પ્રકાર", ["IN", "OUT"])
        qty = st.number_input("જથ્થો", min_value=0.1)
        unit = st.selectbox("એકમ", ["કિલો", "ડબ્બા", "નંગ"])
        i_date = st.date_input("તારીખ")
        if st.form_submit_button("💾 સેવ"):
            data = {"item_name": item_name.upper(), "trans_type": t_type, "quantity": qty, "unit": unit, "entry_date": str(i_date), "remarks": ""}
            supabase.table("inventory").insert(data).execute()
            st.success("✅ સ્ટોક સેવ થયો.")

    st.write("##### 📈 હાલનો સ્ટોક")
    res = supabase.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        st.dataframe(df_inv)

# ==========================================
# 5. લેટર (Letters - Supabase)
# ==========================================
def render_letter_module():
    st.write("#### 📜 પત્ર ટાઇપિંગ")
    with st.form("letter_form", clear_on_submit=True):
        outward_no = st.text_input("જાવક નં")
        letter_date = st.date_input("તારીખ")
        recipient = st.text_area("પ્રતિ")
        subject = st.text_input("વિષય")
        body_text = st.text_area("લખાણ")
        if st.form_submit_button("💾 પત્ર સેવ કરો"):
            data = {"outward_no": outward_no, "ref_no": "N/A", "letter_date": str(letter_date), "recipient": recipient, "subject": subject, "body_text": body_text}
            supabase.table("letters").insert(data).execute()
            st.success("✅ પત્ર સેવ થઈ ગયો!")

# ==========================================
# 6. એડમિન ડેશબોર્ડ (Dashboard - Supabase)
# ==========================================
def render_dashboard_module():
    if not is_admin: return st.error("❌ પરવાનગી નથી.")
    
    # રકમનો સરવાળો કાઢવા માટે
    res_b = supabase.table("bookings").select("amount").execute()
    c_jmn = sum(item["amount"] for item in res_b.data) if res_b.data else 0.0
    
    res_d = supabase.table("donations").select("amount").execute()
    c_don = sum(item["amount"] for item in res_d.data) if res_d.data else 0.0
    
    res_e = supabase.table("expenses").select("amount").execute()
    tot_exp = sum(item["amount"] for item in res_e.data) if res_e.data else 0.0
    
    net_bal = (c_jmn + c_don) - tot_exp

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🍲 જમણવાર આવક", f"₹ {c_jmn:,.2f}")
    m2.metric("🎁 સામાન્ય દાન", f"₹ {c_don:,.2f}")
    m3.metric("📤 કુલ ખર્ચ", f"₹ {tot_exp:,.2f}")
    m4.metric("💵 હાથ પર બાકી", f"₹ {net_bal:,.2f}")

    st.markdown("---")
    st.write("### 📋 બુકિંગ યાદી")
    res_all = supabase.table("bookings").select("*").order("id", desc=True).execute()
    if res_all.data:
        df_b = pd.DataFrame(res_all.data)
        st.dataframe(df_b)

# ==========================================
# RUN MODULES
# ==========================================
if is_admin or is_operator:
    if t_booking:
        with t_booking: render_booking_module()
        with t_donation: render_donation_module()
        with t_expense: render_expense_module()
        with t_inventory: render_inventory_module()
        with t_letter: render_letter_module()
        with t_dashboard: render_dashboard_module()
elif selected_menu:
    if selected_menu == "🍲 જમણવાર બુકિંગ":
        with t_booking: render_booking_module()
    elif selected_menu == "🎁 સામાન્ય દાન (Donation)":
        with t_donation: render_donation_module()
