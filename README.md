# betterPrintToPDF

A Python-based tool for capturing high-quality, full-page screenshots and exporting them as PDFs.  
Supports both desktop and mobile views, with customizable pre- and post-screenshot logic per site.

---

## ✨ Features
- Capture **full-page screenshots** (stitched scrolling).
- Export screenshots into **PDF format**.
- Supports **desktop and mobile resolutions**.
- Customizable **pre-screenshot actions**:
  - Click to close popups/cookie banners.
  - Wait for elements/animations to load.
  - Run custom JavaScript.
- Customizable **post-screenshot actions**:
  - Capture additional elements.
  - Handle dropdowns, carousels, or hidden text.
- Supports **concurrent jobs** with threading.
- Exclude specific URLs from being processed.

---

## 📦 Requirements

This project uses **Python 3.9+** (earlier versions may work, but not tested).  

Install dependencies with:

```bash
pip install -r requirements.txt
````

### `requirements.txt`

```txt
# Web scraping / async
scrapy
twisted
crochet

# Browser automation
selenium

# Images / PDFs
Pillow
pypdf
```

---

## 🚀 Usage

1. Clone the repository:

   ```bash
   git clone https://github.com/ryguy0601/betterPrintToPDF.git
   cd betterPrintToPDF
   ```

2. (Optional but recommended) Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the script:

   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

* **Site Settings:** Edit `globals.py` or `beforeScreenChecks`/`afterScreenChecks` in `site_specific.py` to customize behavior per site.
* **Excluded URLs:** Update `excludedURLS` in `site_specific.py` to skip certain pages.
* **Credentials:** If `jobs[job_id]['username']` and `['password']` are provided, they will be injected into URLs automatically.

---

## 🛠️ Example Customization

In `beforeScreenChecks` you can:

```python
if siteName == "Example1":
    args['waitTime'] = 3  # Wait for animations
    args['clickInfo'] = [
        '//button[@id="accept-cookies"]',
        '//div[@class="popup-close"]',
    ]
```

In `afterScreenChecks` you can:

```python
functions['name'].append(screenShotOfElement)
functions['args'].append((url, '//div[@id="carousel"]'))
functions['kwargs'].append({
    'customJS': "console.log('Captured carousel item')"
})
```

---

## 🖥️ ChromeDriver Setup

This project uses Selenium, so you’ll need **Google Chrome** and **ChromeDriver** installed.

* **Windows:**
  Download [ChromeDriver](https://chromedriver.chromium.org/downloads) and place it in your PATH.

* **macOS/Linux:**

  ```bash
  brew install chromedriver    # macOS (Homebrew)
  sudo apt install chromium-chromedriver  # Ubuntu/Debian
  ```

Or let Selenium auto-manage with `webdriver-manager`.

---

## 📜 License

MIT License — feel free to use and modify.

---

## 👨‍💻 Author

Created by [ryguy0601](https://github.com/ryguy0601).


