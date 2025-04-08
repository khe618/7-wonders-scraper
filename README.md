# 🏛️ Seven Wonders Game Data Scraper

This project uses **Playwright** and **Python** to log into [Board Game Arena](https://boardgamearena.com), collect **detailed game data** for *Seven Wonders*, and export it to a CSV file. 

You’ll get per-player stats such as:
- Total score and rank
- Wonder board ID
- Victory points from each category (Civilian, Science, Military, etc.)

---

## 📦 Features

✅ Automatically logs into your BGA account  
✅ Extracts your player ID dynamically  
✅ Scrapes detailed stats for each finished *Seven Wonders* table  
✅ Exports data into a clean `.csv` file for analysis or visualization  

---

## 🚀 Requirements

- Python 3.8+
- Google Chrome or Chromium
- [Playwright](https://playwright.dev/python/) + dependencies

Install everything with:

```bash
pip install -r requirements.txt
playwright install
