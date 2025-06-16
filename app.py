import streamlit as st

# ─── Streamlit Page Config ────────────────────────────────────────────────────
# MUST be the first Streamlit command in your script
st.set_page_config(page_title="LinkedIn AI Agent", layout="wide")

# ─── Imports ───────────────────────────────────────────────────────────────────
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
from bs4 import BeautifulSoup
import google.generativeai as genai

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GOOGLE_API_KEY = "AIzaSyD8sY5E0dj-6yKyXjqaGH3a5CSQYEdI4yo"
genai.configure(api_key=GOOGLE_API_KEY)

# ─── SELENIUM DRIVER SETUP ────────────────────────────────────────────────────
@st.cache_resource
def get_driver():
    try:
        chrome_path = "/usr/bin/google-chrome"
        driver_path = "/usr/local/bin/chromedriver"
        options = webdriver.ChromeOptions()
        options.binary_location = chrome_path
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")

        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        return driver
    except Exception as e:
        st.error(f"❌ Error initializing browser: {e}")
        return None

def ensure_valid_session(driver):
    try:
        _ = driver.current_url
        return True
    except (WebDriverException, SessionNotCreatedException):
        return False

def get_fresh_driver():
    if driver := get_driver():
        try:
            driver.quit()
        except:
            pass
    return get_driver()

# ─── SCRAPING & MESSAGE GENERATION ───────────────────────────────────────────
def scrape_linkedin_profile(driver, url):
    retries = 3
    for attempt in range(retries):
        try:
            if not ensure_valid_session(driver):
                driver = get_fresh_driver()
                if not driver:
                    return None

            if not url.startswith("https://www.linkedin.com/"):
                url = "https://www.linkedin.com/" + url.lstrip("/")
            driver.get(url)
            time.sleep(5)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            name_tag = soup.find("h1")
            name = name_tag.get_text(strip=True) if name_tag else ""

            headline_tag = soup.find("div", class_="text-body-medium")
            headline = headline_tag.get_text(strip=True) if headline_tag else ""

            about = ""
            about_section = soup.find("section", {"id": "about"})
            if about_section:
                t = about_section.find("div", class_="pv-shared-text-with-see-more")
                about = t.get_text(strip=True) if t else ""

            return {"Name": name, "Headline": headline, "About": about}
        except Exception:
            time.sleep(2)
    st.error(f"❌ Failed to scrape {url} after {retries} attempts")
    return None

def generate_fallback_message(name, headline):
    return (
        f"Hi {name.split()[0]},\n\n"
        f"I came across your profile and was impressed by your experience as {headline}. "
        "Looking forward to connecting!"
    )

def generate_message(name, headline, about):
    try:
        prompt = f"""
Write a detailed, personalized LinkedIn connection request to {name}, whose headline is:
"{headline}"

About section:
"{about}"

Requirements:
1. At least 4 lines long
2. Mention their company name if visible
3. Reference recent activity or achievements if mentioned
4. Professional but warm
5. Genuine interest
6. Specific reason for connecting
7. Clear call to action

Format naturally.
"""
        model = genai.GenerativeModel("gemini-1.0-pro")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        st.error(f"❌ Error generating message: {e}")
        return generate_fallback_message(name, headline)

# ─── STREAMLIT UI ─────────────────────────────────────────────────────────────
st.title("🤖 LinkedIn AI Agent")
tabs = st.tabs(["📨 Hyperpersonalization", "🏢 Company Research"])

with tabs[0]:
    st.header("Generate Personalized Messages")
    uploaded = st.file_uploader("Upload CSV of LinkedIn URLs", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        if "URL" not in df.columns:
            st.error("CSV needs a column named 'URL'")
        else:
            driver = get_driver()
            if not driver:
                st.error("Browser init failed. Refresh and retry.")
                st.stop()

            st.warning("Log in to LinkedIn in the popped browser window.")
            driver.get("https://www.linkedin.com/login")
            st.info("After login, click \"Start Generating Messages\" below.")

            if st.button("Start Generating Messages"):
                results = []
                prog = st.progress(0)
                total = len(df)
                for i, row in df.iterrows():
                    data = scrape_linkedin_profile(driver, row["URL"])
                    if data:
                        msg = generate_message(data["Name"], data["Headline"], data["About"])
                        results.append({"URL": row["URL"], "Message": msg})
                    prog.progress((i + 1) / total)

                if results:
                    res_df = pd.DataFrame(results)
                    st.success("✅ Messages ready")
                    st.dataframe(res_df)
                    csv = res_df.to_csv(index=False).encode("utf-8")
                    st.download_button("Download CSV", csv, "messages.csv", "text/csv")
                else:
                    st.error("No messages generated. Check login & URLs.")

with tabs[1]:
    st.header("Find Company Executives")
    company = st.text_input("Company Name")
    if st.button("Search Executives"):
        driver = get_driver()
        st.warning("Log in to LinkedIn in the popped browser window.")
        driver.get("https://www.linkedin.com/login")
        st.info("After login, click \"Search Executives\" again.")
        if company:
            execs = []
            roles = ["CEO", "CTO", "CMO", "COO", "Founder", "VP"]
            for role in roles:
                q = f'site:linkedin.com/in "{role}" "{company}"'
                driver.get(f"https://www.google.com/search?q={q}")
                time.sleep(3)
                bs = BeautifulSoup(driver.page_source, "html.parser")
                for a in bs.select("div.yuRUbf a"):
                    link = a["href"]
                    title = a.get_text()
                    if "linkedin.com/in" in link:
                        execs.append({"Title": title, "LinkedIn URL": link})
            if execs:
                edf = pd.DataFrame(execs)
                st.success(f"Found {len(execs)} execs")
                st.dataframe(edf)
                csv2 = edf.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv2, "execs.csv", "text/csv")
            else:
                st.info("No executives found.")
