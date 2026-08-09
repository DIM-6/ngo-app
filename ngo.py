import os
import time
import glob
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("=========================================================")
print("   VSK Attendance - Permanent Robust Automation          ")
print("=========================================================\n")

# ૧. સેટઅપ અને ઓથેન્ટિકેશન
USER_EMAIL = "surat_gjvsk@DIRECTORATE12.onmicrosoft.com"
USER_PASSWORD = os.environ.get("FABRIC_PASSWORD")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

download_dir = os.path.join(os.getcwd(), 'downloads')
os.makedirs(download_dir, exist_ok=True)

# જૂની કોઈ ફાઈલ પડી હોય તો તેને ક્લિયર કરી દઈએ જેથી કન્ફ્યુઝન ના થાય
for f in glob.glob(os.path.join(download_dir, "*")):
    try: os.remove(f)
    except: pass

# ઓરિજિનલ રિપોર્ટ લિંક્સ (અહીં Student પહેલો અને Teacher બીજો છે)
report_urls = [
    "https://app.fabric.microsoft.com/groups/31be3eed-4675-4c08-bfd1-0b3677e960b7/rdlreports/eaf01d7d-b0ee-468d-9a34-3bce2444dbed?experience=fabric-developer",
    "https://app.fabric.microsoft.com/groups/31be3eed-4675-4c08-bfd1-0b3677e960b7/rdlreports/07d729df-4c6d-427a-be27-4022051b5997?experience=fabric-developer"
]

def click_element_safely(driver, wait, xpaths):
    for xpath in xpaths:
        try:
            elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
            time.sleep(1)
            try: elem.click()
            except: driver.execute_script("arguments[0].click();", elem)
            return True
        except:
            continue
    return False

# સ્માર્ટ ડાઉનલોડ ટ્રેકર - ફાઈલ પૂરી ડાઉનલોડ ના થાય ત્યાં સુધી રાહ જોશે
def wait_for_downloads(expected_count, timeout=90):
    print(f" -> {expected_count} ફાઈલ ડાઉનલોડ થવાની રાહ જોઈ રહ્યા છીએ...")
    end_time = time.time() + timeout
    while time.time() < end_time:
        # .crdownload (અધૂરી ફાઈલ) ને ગણશે નહીં, માત્ર પૂરી .xlsx ને જ ગણશે
        files = [f for f in glob.glob(os.path.join(download_dir, "*.xlsx")) if not f.endswith('.crdownload')]
        if len(files) == expected_count:
            print(" ✓ ડાઉનલોડ પૂર્ણ થઈ ગયું!")
            return sorted(files, key=os.path.getctime)
        time.sleep(3)
    print(" ! Timeout: ડાઉનલોડમાં વધુ પડતો સમય લાગ્યો.")
    return sorted([f for f in glob.glob(os.path.join(download_dir, "*.xlsx")) if not f.endswith('.crdownload')], key=os.path.getctime)

def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })

    wait = WebDriverWait(driver, 15)

    try:
        driver.get(report_urls[0])
        time.sleep(5)

        email_elements = driver.find_elements(By.XPATH, '//*[@id="email"]')
        if len(email_elements) > 0 and email_elements[0].is_displayed():
            print("Logging in...")
            email_field = email_elements[0]
            email_field.clear()
            email_field.send_keys(USER_EMAIL)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submitBtn"]'))).click()
            time.sleep(3)

            pass_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="i0118"]')))
            pass_field.clear()
            for char in USER_PASSWORD:
                pass_field.send_keys(char)
                time.sleep(0.05)
            time.sleep(1)

            try: driver.find_element(By.XPATH, '//*[@id="idSIButton9" or @type="submit"]').click()
            except: pass_field.submit()
            time.sleep(4)
            
            try: driver.find_element(By.XPATH, '//*[@id="idSIButton9" or contains(text(), "Yes")]').click()
            except: pass

        home_xpaths = ['//*[@id="home"]/span', "//button[contains(., 'Home')]"]
        export_xpaths = ['//*[@id="id__114"]', '//*[@id="id__113"]', "//button[contains(@aria-label, 'Export')]", "//button[contains(., 'Export')]"]
        excel_xpaths = [
            '//*[@id="id__114-menu"]/div/ul/li[1]/button/div/span',
            '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div/div[2]/div/div/div/div/div/div[1]/button/span',
            "//button[contains(., 'Microsoft Excel (.xlsx)')]", 
            "//button[contains(., 'Excel')]"
        ]

        expected_files = 1
        for index, url in enumerate(report_urls, start=1):
            print(f"Opening report {index}...")
            driver.get(url)
            time.sleep(20)

            driver.switch_to.default_content()
            click_element_safely(driver, wait, home_xpaths)
            time.sleep(2)
            
            click_element_safely(driver, wait, export_xpaths)
            time.sleep(3)
            
            click_element_safely(driver, wait, excel_xpaths)
            print(f" -> Excel બટન દબાવી દીધું છે (Report {index})...")
            
            # સ્માર્ટ ટ્રેકર: જ્યાં સુધી ૧ (પછી ૨) ફાઈલ ના દેખાય ત્યાં સુધી કોડ આગળ નહીં વધે
            wait_for_downloads(expected_count=expected_files)
            expected_files += 1
            
            driver.switch_to.default_content()

    except Exception as e:
        print(f"Error in UI Automation: {e}")
    finally:
        driver.quit()

    print("\n--- Processing & Uploading to Supabase ---")
    all_excel = sorted(glob.glob(os.path.join(download_dir, '*.xlsx')), key=os.path.getctime)

    if len(all_excel) < 2:
        print(f"Error: 2 ફાઈલો જોઈતી હતી પણ માત્ર {len(all_excel)} મળી! ડાઉનલોડ નિષ્ફળ.")
        return

    # પહેલો સ્ટુડન્ટ ડાઉનલોડ થયો એટલે index 0, બીજો ટીચર એટલે index 1
    stu_path = all_excel[0]
    tch_path = all_excel[1]
    
    print(f"Student File: {os.path.basename(stu_path)}")
    print(f"Teacher File: {os.path.basename(tch_path)}")

    df_stu = pd.read_excel(stu_path, engine='openpyxl')
    df_tch = pd.read_excel(tch_path, engine='openpyxl')
    df_stu.columns = df_stu.columns.astype(str).str.strip()
    df_tch.columns = df_tch.columns.astype(str).str.strip()
    df_stu['SCHOOL_CODE'] = df_stu['SCHOOL_CODE'].astype(str).str.strip()
    df_tch['SCHOOL_CODE'] = df_tch['SCHOOL_CODE'].astype(str).str.strip()

    df_merged = pd.merge(df_stu, df_tch, on='SCHOOL_CODE', how='outer')
    df_merged['Date'] = datetime.now().strftime('%Y-%m-%d')

    def get_attendance_status(row):
        stu_val = row.get('STUDENTS_SUBMITTED', 0)
        tch_val = row.get('TEACHERS_SUBMITTED', 0)
        stu_pending = pd.isna(stu_val) or str(stu_val).strip() in ['', 'nan', '0', '0.0']
        tch_pending = pd.isna(tch_val) or str(tch_val).strip() in ['', 'nan', '0', '0.0']
        if stu_pending and tch_pending: return 'Both Pending'
        elif stu_pending: return 'Student Pending'
        elif tch_pending: return 'Teacher Pending'
        else: return 'Submitted'

    df_merged['Attendance_Status'] = df_merged.apply(get_attendance_status, axis=1)
    df_merged = df_merged.where(pd.notnull(df_merged), None)

    records = df_merged.to_dict('records')
    print(f"Uploading {len(records)} rows to Supabase...")
    supabase.table('daily_attendance').insert(records).execute()
    print("✓ Success! Data uploaded.")

if __name__ == "__main__":
    main()
