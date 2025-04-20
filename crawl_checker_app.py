import streamlit as st
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try importing html escape depending on Python version
try:
    import html
except ImportError:
    import cgi as html  # fallback for older Python versions

st.set_page_config(page_title="Crawlability Checker", layout="wide")

st.title("🌐 MSA Website Crawlability Checker")
st.markdown("""
Paste a list of websites (one per line) below.
The app will:
- Check if each website can be crawled normally
- Detect if it provides a sitemap
- Recommend the best method for crawling
- Suggest available crawling methods (HTML, Sitemap, API, RSS)
""")

# User input area
input_text = st.text_area("📥 Enter websites (one per line):", height=300)

# Known APIs
def get_known_api(domain):
    known_apis = {
        "paperswithcode.com": "https://paperswithcode.com/api/v1/",
        "github.com": "https://api.github.com/",
        "openlibrary.org": "https://openlibrary.org/developers/api",
    }
    return known_apis.get(domain, None)

# Core check function
def check_site(url, user_agent='*', timeout=5):
    try:
        parsed_url = urlparse(url.strip())
        domain = parsed_url.netloc
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"

        response = requests.get(robots_url, timeout=timeout)
        if response.status_code != 200:
            return {
                "Website": url,
                "Crawling Allowed": f"❌ No (HTTP {response.status_code})",
                "Sitemap Found": "Unknown",
                "Known API": "Unknown",
                "Best Access Method": "❌ No Access",
                "All Crawling Methods Available": "Unknown",
                "Crawl Delay": "Unknown",
                "JS-Heavy Site": "Unknown",
                "RSS Feed Available": "Unknown",
                "Allowed Paths": "Unknown",
                "Disallowed Paths": "Unknown",
                "Advanced Crawling Suggestion": "Use headless browser like Playwright or Selenium",
                "Sitemap Preview": "N/A",
                "Crawlability Score": 0,
                "Suggested Use": "🔴 Not Recommended"
            }

        content = response.text
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(content.splitlines())
        crawl_allowed = rp.can_fetch(user_agent, url)
        crawl_delay = rp.crawl_delay(user_agent)

        sitemap_matches = re.findall(r'(?i)^Sitemap:\s*(.+)', content, re.MULTILINE)
        sitemap_info = ', '.join(sitemap_matches) if sitemap_matches else None

        allowed_paths = re.findall(r'^Allow:\s*(.*)', content, re.MULTILINE)
        disallowed_paths = re.findall(r'^Disallow:\s*(.*)', content, re.MULTILINE)

        rss_found = "rss" in content.lower() or "feed" in content.lower()
        js_heavy = any(k in content.lower() for k in ["webpack", "window.__INITIAL_STATE__", "react", "vue", "next.js"])

        api_url = get_known_api(domain)

        methods = []
        if crawl_allowed:
            methods.append("Normal Crawling")
        if sitemap_info:
            methods.append("Sitemap")
        if api_url:
            methods.append("API")
        if rss_found:
            methods.append("RSS")

        if sitemap_info:
            best_method = "📦 Sitemap (Recommended)"
        elif crawl_allowed:
            best_method = "✅ Normal Crawling"
        else:
            best_method = "❌ No Access"

        # Intelligent tool suggestion based on JS-heavy content and crawlability
        if crawl_allowed and not js_heavy:
            tool_suggestion = "🟢 Use requests + BeautifulSoup (lightweight & fast)"
        elif js_heavy and crawl_allowed:
            tool_suggestion = "🟡 Use Playwright, Puppeteer, or Selenium (JS-rendered content)"
        elif not crawl_allowed:
            tool_suggestion = "🔴 Crawling blocked. Consider Playwright or Splash (headless browser), or look for public APIs"
        else:
            tool_suggestion = "⚠️ Fallback: Try headless tools (e.g., Splash, Playwright)"

        suggestion = tool_suggestion

        score = 0
        if crawl_allowed:
            score += 30
        if sitemap_info:
            score += 30
        if rss_found:
            score += 15
        if api_url:
            score += 15
        if not js_heavy:
            score += 10

        if "recipes" in url or "food" in url:
            project_type = "🍲 Recipe Extraction"
        elif "news" in url or "times" in url or "aljazeera" in url:
            project_type = "📰 News Aggregator"
        elif "jobs" in url or "career" in url or "remote" in url:
            project_type = "💼 Job Crawler"
        elif "books" in url or "openlibrary" in url:
            project_type = "📚 Book Recommender"
        elif "travel" in url or "trip" in url or "expedia" in url:
            project_type = "🌍 Travel Deals Monitor"
        elif api_url:
            project_type = "📡 API-based Dashboard"
        elif sitemap_info:
            project_type = "🔍 Sitemap-based Indexer"
        else:
            project_type = "🧪 Experimental / Headless Only"

        sitemap_preview = "N/A"
        try:
            if sitemap_matches:
                first = sitemap_matches[0]
                sm_resp = requests.get(first, timeout=10)
                if sm_resp.status_code == 200:
                    urls = re.findall(r"<loc>(.*?)</loc>", sm_resp.text)
                    sitemap_preview = "\n".join(urls[:5]) if urls else "No URLs Found"
        except:
            sitemap_preview = "Failed to preview"

        return {
            "Website": url,
            "Crawling Allowed": "✅ Yes" if crawl_allowed else "❌ No",
            "Sitemap Found": sitemap_info or "No sitemap",
            "Known API": api_url if api_url else "None",
            "Best Access Method": best_method,
            "All Crawling Methods Available": ", ".join(methods) if methods else "None",
            "Crawl Delay": f"{crawl_delay} sec" if crawl_delay else "Not specified",
            "JS-Heavy Site": "🧠 Likely JS-Rendered" if js_heavy else "✅ Mostly HTML",
            "RSS Feed Available": "✅ Yes" if rss_found else "❌ No",
            "Allowed Paths": ", ".join(allowed_paths) if allowed_paths else "None specified",
            "Disallowed Paths": ", ".join(disallowed_paths) if disallowed_paths else "None specified",
            "Advanced Crawling Suggestion": suggestion,
            "Sitemap Preview": sitemap_preview,
            "Crawlability Score": score,
            "Suggested Use": project_type
        }

    except Exception as e:
        return {
            "Website": url,
            "Crawling Allowed": f"❌ No (Error: {e})",
            "Sitemap Found": "Unknown",
            "Known API": "Unknown",
            "Best Access Method": "❌ No Access",
            "All Crawling Methods Available": "Unknown",
            "Crawl Delay": "Unknown",
            "JS-Heavy Site": "Unknown",
            "RSS Feed Available": "Unknown",
            "Allowed Paths": "Unknown",
            "Disallowed Paths": "Unknown",
            "Advanced Crawling Suggestion": "Use headless browser like Playwright or Selenium",
            "Sitemap Preview": "N/A",
            "Crawlability Score": 0,
            "Suggested Use": "🔴 Not Recommended"
        }

# UI handler
if st.button("🔍 Check Crawlability"):
    urls = [line.strip() for line in input_text.strip().splitlines() if line.strip()]
    if not urls:
        st.warning("Please enter at least one website.")
    else:
        st.info("⏳ Checking... please wait.")
        results = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(check_site, site): site for site in urls}
            for future in as_completed(future_to_url):
                results.append(future.result())

        df = pd.DataFrame(results)
        st.success("✅ Crawlability Check Complete!")

        for row in results:
            st.markdown(f"""
<details style="border: 1px solid #444; border-radius: 10px; padding: 10px; margin-bottom: 15px; background-color: #111;">
  <summary style="font-size: 18px;">
    🔗 <a href="{row['Website']}" target="_blank" style="color: #1f77b4;">{row['Website']}</a> — <b>{row['Best Access Method']}</b>
  </summary>
  <div style="line-height: 1.6;">
    <p><b>🛡️ Crawling Allowed:</b> {row['Crawling Allowed']}</p>
    <p><b>📦 Sitemap:</b> {html.escape(row['Sitemap Found'])}</p>
    <p><b>🧠 JS-Heavy Site:</b> {row['JS-Heavy Site']}</p>
    <p><b>📰 RSS Feed:</b> {row['RSS Feed Available']}</p>
    <p><b>⚙️ Known API:</b> {row['Known API']}</p>
    <p><b>⏱️ Crawl Delay:</b> {row['Crawl Delay']}</p>
    <p><b>🚧 Disallowed Paths:</b><br><code>{html.escape(row['Disallowed Paths'])}</code></p>
    <p><b>✅ Allowed Paths:</b><br><code>{html.escape(row['Allowed Paths'])}</code></p>
    <p><b>🔍 Sitemap Preview:</b><br><code>{html.escape(row['Sitemap Preview'].replace(',', '<br>'))}</code></p>
    <p><b>🛠️ All Crawling Methods:</b> {row['All Crawling Methods Available']}</p>
    <p><b>💡 Suggestion:</b> {row['Advanced Crawling Suggestion']}</p>
    <p><b>🔧 Suggested Use:</b> {row['Suggested Use']}</p>

<p><b>📊 Crawlability Score:</b> {row['Crawlability Score']}%</p>
<div style="width: 100%; background: #333; border-radius: 5px;">
  <div style="width: {row['Crawlability Score']}%; background: {'#4CAF50' if row['Crawlability Score'] > 70 else '#FFC107' if row['Crawlability Score'] > 40 else '#F44336'}; padding: 5px; color: white; text-align: center; border-radius: 5px;">
    {row['Crawlability Score']}%
  </div>
</div>
</p>
  </div>
</details>
""", unsafe_allow_html=True)

        # Download CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download as CSV", csv, "crawlability_report.csv", "text/csv")
