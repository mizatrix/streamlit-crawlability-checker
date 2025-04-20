# 🌐 Website Crawlability Checker

A Streamlit web app that checks whether websites can be crawled by bots and search engines. This tool evaluates factors such as robots.txt rules, sitemap availability, RSS feeds, known APIs, and JavaScript rendering to give each site a **crawlability score** and suggestions for crawling tools.

## 🚀 Features

- ✅ Detects if crawling is allowed via `robots.txt`
- 🗺️ Checks for available sitemaps
- 🧠 Identifies JS-heavy websites
- 📰 Checks for RSS feed availability
- 🛠 Suggests the best crawling method (HTML, Sitemap, API, Headless)
- 📊 Generates a crawlability score with visual feedback
- 📥 Export results as CSV


## 🧑‍💻 Technologies Used

- [Streamlit](https://streamlit.io/)
- [Python](https://www.python.org/)
- `reppy`, `requests`, `concurrent.futures`, and other standard libraries

## 📦 Installation

```bash
git clone https://github.com/mizatrix/streamlit-crawlability-checker.git
cd streamlit-crawlability-checker
pip install -r requirements.txt
streamlit run crawl_checker_app.py
