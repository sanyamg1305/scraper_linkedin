import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import google.generativeai as genai
import chromedriver_autoinstaller

# --------------- CONFIG ----------------
# Configure Gemini API
GOOGLE_API_KEY = "AIzaSyD8sY5E0dj-6yKyXjqaGH3a5CSQYEdI4yo"
genai.configure(api_key=GOOGLE_API_KEY)

# Set up Selenium
@st.cache_resource
def get_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-notifications')
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        options.binary_location = "/usr/bin/chromium"
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        return driver
    except Exception as e:
        st.error(f"Error initializing browser: {str(e)}")
        return None

def ensure_valid_session(driver):
    try:
        # Try to get the current URL to check if session is valid
        driver.current_url
        return True
    except (WebDriverException, SessionNotCreatedException):
        return False

def get_fresh_driver():
    try:
        driver = get_driver()
        if driver:
            driver.quit()  # Close any existing session
        return get_driver()
    except Exception as e:
        st.error(f"Error refreshing browser session: {str(e)}")
        return None

# ---------------- HYPERPERSONALIZATION MODULE ----------------
def scrape_linkedin_profile(driver, url):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if not ensure_valid_session(driver):
                driver = get_fresh_driver()
                if not driver:
                    return None
                
            if not url.startswith('https://www.linkedin.com/'):
                url = 'https://www.linkedin.com/' + url.lstrip('/')
            driver.get(url)
            time.sleep(5)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            name = soup.find('h1')
            name = name.text.strip() if name else ""

            headline_tag = soup.find('div', class_='text-body-medium')
            headline = headline_tag.text.strip() if headline_tag else ""

            about_section = soup.find('section', {'id': 'about'})
            about_text = ""
            if about_section:
                about_text_tag = about_section.find('div', class_='pv-shared-text-with-see-more')
                if about_text_tag:
                    about_text = about_text_tag.text.strip()

            return {
                "Name": name,
                "Headline": headline,
                "About": about_text
            }
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                st.error(f"Error scraping LinkedIn profile after {max_retries} attempts: {str(e)}")
                return None
            time.sleep(2)  # Wait before retrying
            driver = get_fresh_driver()
            if not driver:
                return None

def generate_fallback_message(name, headline):
    """Generate a simple message when API is not available"""
    return f"""Hi {name.split()[0]},

I came across your profile and was impressed by your experience as {headline}. Your professional journey and expertise in this field caught my attention.

I would love to connect and learn more about your work and experiences. It would be great to exchange insights and potentially collaborate in the future.

Looking forward to connecting!"""

def generate_message(name, headline, about):
    try:
        prompt = f"""
        Write a detailed, personalized LinkedIn connection request to {name}, whose headline is:
        "{headline}"

        About section:
        "{about}"

        Requirements:
        1. Message should be at least 4 lines long
        2. Mention their company name if visible in their profile
        3. Reference their recent activity or achievements if mentioned
        4. Keep it professional but warm and engaging
        5. Show genuine interest in their work
        6. Include a specific reason for connecting
        7. End with a clear call to action

        Format the message in a natural, conversational tone.
        """

        model = genai.GenerativeModel('gemini-1.0-pro')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating message: {str(e)}")
        return generate_fallback_message(name, headline)

# ---------------- COMPANY RESEARCH MODULE ----------------
def search_execs_on_google(company_name, driver):
    exec_keywords = ["CEO", "CTO", "CMO", "COO", "Founder", "VP"]
    exec_data = []
    for role in exec_keywords:
        query = f"site:linkedin.com/in \"{role}\" \"{company_name}\""
        driver.get(f"https://www.google.com/search?q={query}")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for result in soup.select('div.yuRUbf a'):
            link = result['href']
            title = result.get_text()
            if "linkedin.com/in" in link:
                exec_data.append({"Title": title, "LinkedIn URL": link})
    return exec_data

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="LinkedIn AI Agent", layout="wide")
st.title("🤖 LinkedIn AI Agent")

tab1, tab2 = st.tabs(["📨 Hyperpersonalization", "🏢 Company Research"])

with tab1:
    st.header("Generate Personalized LinkedIn Messages")
    uploaded_file = st.file_uploader("Upload CSV with LinkedIn Profile URLs", type=['csv'])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "URL" not in df.columns:
            st.error("CSV must contain a column named 'URL'")
        else:
            driver = get_driver()
            if not driver:
                st.error("Failed to initialize browser. Please refresh the page and try again.")
                st.stop()
                
            st.warning("Please log in to LinkedIn manually in the opened browser.")
            try:
                driver.get("https://www.linkedin.com/login")
                time.sleep(2)  # Give time for the page to load
                if "login" not in driver.current_url.lower():
                    driver.get("https://www.linkedin.com/login")
            except Exception as e:
                st.error(f"Error loading LinkedIn: {str(e)}")
                st.info("Please try refreshing the page and starting again.")
                st.stop()
            st.info("After logging in, go back to Streamlit and start scraping.")

            if st.button("Start Generating Messages"):
                messages = []
                progress_bar = st.progress(0)
                total_profiles = len(df)
                
                for i, row in df.iterrows():
                    try:
                        profile_data = scrape_linkedin_profile(driver, row['URL'])
                        if profile_data:
                            message = generate_message(profile_data['Name'], profile_data['Headline'], profile_data['About'])
                            messages.append({
                                "LinkedIn URL": row['URL'],
                                "Customized Message": message
                            })
                    except Exception as e:
                        st.error(f"Error processing profile {row['URL']}: {str(e)}")
                        continue
                        
                    # Update progress
                    progress = (i + 1) / total_profiles
                    progress_bar.progress(progress)
                
                if messages:
                    result_df = pd.DataFrame(messages)
                    st.success("Messages generated!")
                    st.dataframe(result_df)
                    
                    # Create and download CSV
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Messages CSV",
                        data=csv,
                        file_name="linkedin_messages.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("No messages were generated. Please check the LinkedIn login and try again.")

with tab2:
    st.header("Find Executives at a Company")
    company_name = st.text_input("Enter Company Name")

    if st.button("Search Executives"):
        driver = get_driver()
        st.warning("Please log in to LinkedIn manually in the opened browser.")
        driver.get("https://www.linkedin.com/login")
        st.info("After logging in, go back to Streamlit and start the search.")

        execs = search_execs_on_google(company_name, driver)
        if execs:
            exec_df = pd.DataFrame(execs)
            st.success(f"Found {len(execs)} executives!")
            st.dataframe(exec_df)
            csv = exec_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv, file_name="executives.csv", mime="text/csv")
        else:
            st.info("No executives found. Try a broader company name or different spelling.")
