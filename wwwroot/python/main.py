from math import e
import site
import time, os, datetime,sys,json, shutil
from threading import Thread

from spider.getWebMap import *
from customSiteCode import *
from globals import *


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from PIL import Image
from pypdf import PdfWriter
from datetime import datetime, timedelta


def stitch_PNG_slices_vertically(images):
    """
    Stitches a list of PIL Image objects vertically into a single image.

    :param images: List of PIL.Image objects
    :param output_path: Path to save the stitched PNG
    """

    if not images:
        raise ValueError("Image list is empty.")

    # Determine final width and height
    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)

    # Create a blank image with that size
    stitched_img = Image.new("RGB", (max_width, total_height))

    # Paste images one after another vertically
    current_y = 0
    for img in images:
        stitched_img.paste(img, (0, current_y))
        current_y += img.height

    return stitched_img

def get_files(directory_path):
    """
    Counts the number of files in a specified directory, non-recursively.
    """
    try:
        files = [
            f for f in os.listdir(directory_path)
            if os.path.isfile(os.path.join(directory_path, f))
        ]
        return files
    except FileNotFoundError:
        print(f"Error: Directory '{directory_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

def png_to_pdf(png_path, pdf_path):
    """Converts a single PNG image to a PDF file using Pillow."""

    try:
        image = Image.open(png_path)
        # Pillow can't save RGBA images (with transparency) directly to PDF.
        # Convert to RGB if necessary.
        if image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(pdf_path, "PDF")
    except Exception as e:
        print(f"Error converting '{png_path}': {e}\n")

def merge_pdfs(pdfLst, output_filename, job_id):
    cleaned_pdfLst = []
    for val in pdfLst:
        try:
            int(val.split(".")[0])
            if val.split(".")[1] == 'pdf':
                cleaned_pdfLst.append(val)
        except:
            pass
    pdfLst = cleaned_pdfLst
    pdfLst = sorted(
        pdfLst, key=lambda x: int(x.split(".")[0])
    )  # sorts the files in numerican order rather than alphabetically
    merger = PdfWriter()
    for pdf in pdfLst:
        path = os.path.join(downloadDIR, job_id, pdf)
        merger.append(path)
    merger.write(output_filename)
    merger.close()
    print(f"PDFs merged successfully into {output_filename}\n")

def driverSetUp(res):
    if chromeDriverPath:
        service = Service(executable_path=chromeDriverPath)

    options = Options()
    #works
    options.add_argument("--headless=new")  # headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")


    if res == "desktop":
        options.add_argument("window-size=1920,1080")
    else:
        options.add_argument("window-size=393,852")

    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": downloadDIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    if chromeDriverPath:
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    driver.set_window_position(0, 0)

    return driver


def takeScreenShot(
    job_id,
    curPage,
    driver,
    url,
    siteName,
    clickInfo=None,  # name of element xPAth
    scroll_step=None,
    scroll_pause=0.00,
    scroll_selector='window',#tell the function which element it needs to scroll on, default is the whole page(use css selector)
    customJS='',
    waitTime=0,
    waitUntil=None, #taken as a list, first index is selector type Ex:By.CSS_SELECTOR or By.XPATH, the second index being the path of the chosen selector type
):
    if scroll_step == None: #default val
        scroll_step = driver.execute_script('return window.innerHeight/3')
    global downloadDIR
    driver.get(url)
    driver.refresh()#fixes most page not loading problems
    driver.execute_script("""//instant animations
            style = document.createElement('style');
            style.innerHTML = `* {animation-duration: 0s !important;animation-delay: 0s !important;transition-duration: 0s !important;transition-delay: 0s !important;}`;
            document.head.appendChild(style);
    """)
    if scroll_selector != 'window':
        driver.execute_script('let style = document.createElement("style");'+
        f'style.innerHTML = "{scroll_selector}'+'::-webkit-scrollbar{scrollbar-width: none;-ms-overflow-style: none; display: none; }";'+
        'document.head.appendChild(style);')
        scroll_EL = f"document.querySelector('{scroll_selector}')"
    else:
        scroll_EL = 'window'

    if clickInfo:
        for click in clickInfo:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, click))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                try:
                    element.click()
                except:
                    driver.execute_script("arguments[0].click();", element)
                time.sleep(2)
            except Exception as e:
                print("\nCouldn't click:", click, "| Page:", curPage,"\n")
    time.sleep(1)

    total_width = driver.execute_script("return document.body.scrollWidth")
    if scroll_EL == 'window':
        viewport_height = driver.execute_script(f"return {scroll_EL}.innerHeight;")
    else:
        viewport_height = driver.execute_script(f"return {scroll_EL}.getBoundingClientRect().height;")

    slices = []
    y = 0
    part_index = 1

    screenshot_filename = os.path.join(downloadDIR, job_id,'slice', f"page_{curPage}_slice_{part_index}.png")
    os.makedirs(os.path.dirname(screenshot_filename), exist_ok=True)
    prev_end_crop = viewport_height-scroll_step
    stop = False
    time.sleep(waitTime)

    driver.execute_script(f"document.documentElement.style.scrollBehavior = 'auto' // prevent scroll animation;{scroll_EL}.scrollTo(0, 0);")
    while not stop:
        if waitUntil:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((waitUntil[0], waitUntil[1]))
            )
        driver.execute_script(customJS)
        driver.execute_script("""
            //hides scroll bar
             let style = document.createElement('style');
             style.innerHTML = `
                 *::-webkit-scrollbar { display: none; }
                 body {
                    overflow: hidden !important;
                    scrollbar-width: none !important;
                    -ms-overflow-style: none !important;
                    position: relative !important;
                    min-width: 100vw !important;
                    min-height: 100vh !important;
                 }
             `;
             document.head.appendChild(style);
            //instant animations
             style = document.createElement('style');
             style.innerHTML = `
               * {
                 animation-duration: 0s !important;
                 animation-delay: 0s !important;
                 transition-duration: 0s !important;
                 transition-delay: 0s !important;
               }
             `;
             document.head.appendChild(style);
             document.documentElement.style.scrollBehavior = 'auto' // prevent scroll animation

            // Remove sticky/fixed elements that are visible
            document.querySelectorAll('*').forEach(el => {
              style = getComputedStyle(el);
              const pos = style.position;
              const rect = el.getBoundingClientRect();

              const isVisible = (
                rect.width > 0 &&
                rect.height > 0 &&
                style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                el.offsetParent !== null
              );

              if (isVisible && ['fixed', 'sticky'].includes(pos)) {
                el.style.position = 'static';
                el.style.top = 'unset';
                el.style.bottom = 'unset';
                el.style.zIndex = '1';
              }
            });
        """)


        if scroll_EL == 'window':
            prev_y = driver.execute_script(f"return {scroll_EL}.scrollY;")
        else:
            prev_y = driver.execute_script(f"return {scroll_EL}.scrollTop;")
        driver.execute_script(f"{scroll_EL}.scrollTo(0, {y});")
        time.sleep(scroll_pause)
        if scroll_EL == 'window':
            y = driver.execute_script(f"return {scroll_EL}.scrollY;")
        else:
            y = driver.execute_script(f"return {scroll_EL}.scrollTop;")

        screenshot_filename = os.path.join(downloadDIR, job_id,'slice', f"page_{curPage}_slice_{part_index}.png")


        driver.save_screenshot(screenshot_filename)

        img = Image.open(screenshot_filename)

        # Crop the top slice_height pixels from the screenshot
        if part_index == 1:
            start_crop = 0
            end_crop = img.height - scroll_step
        elif part_index == 2:
            start_crop = prev_end_crop - y
            end_crop = img.height - scroll_step
        elif y - prev_y == 0:
            stop = True
            start_crop = end_crop - (y - prev_y)
            end_crop = img.height
        else:
            start_crop = prev_end_crop - y
            end_crop = img.height - scroll_step

        slice_img = img.crop((0, start_crop, total_width, end_crop))
        # print(f"partIndex: {part_index},Start: {start_crop+y}, end: {end_crop+y} Start crop:{start_crop}, end crop: {end_crop}, deltY: {y-prev_y}")

        if part_index != 1 and start_crop + y != prev_end_crop:
            print("images dont line up", curPage)
            print(start_crop + y, prev_end_crop)
            slice_img = img.crop((0, prev_end_crop - y, total_width, end_crop))

        prev_end_crop = end_crop + y

        slices.append(slice_img)
        os.remove(screenshot_filename)
        if not stop:
            y += scroll_step
        part_index += 1

    # Stitch slices vertically
    final_image = stitch_PNG_slices_vertically(slices)
    final_image.save(os.path.join(downloadDIR, job_id, f"{curPage}.png"))

    png_name = os.path.join(downloadDIR, job_id, f"{curPage}.png")
    pdf_name = os.path.join(downloadDIR, job_id, f"{curPage}.pdf")

    png_to_pdf(png_name, pdf_name)
    while not os.path.exists(pdf_name):
        time.sleep(.5)
    os.remove(png_name)

def screenShotOfElement(
    job_id,
    curPage,
    driver,
    url,
    siteName,
    elXpath,
    clickInfo=None,  # list of element xPaths to click
    scroll_step=200,
    scroll_pause=0.00,
    scroll_selector='window',  # CSS selector for scrollable element, default is whole page
    customJS='',
    waitUntil=None,  # tuple of (By.TYPE, selector) to wait for after clicks
    max_wait_time=5,  # maximum time to wait for elements
):
    """
    Takes a screenshot of a specific element on a webpage.
    
    Args:
        url (str): The URL to navigate to
        driver: WebDriver instance
        curPage (int): Current page number for naming
        siteName (str): Name of the site
        job_id (str): Job identifier
        elXpath (str): XPath of the element to screenshot
        clickInfo (list, optional): List of XPath selectors to click before screenshot
        scroll_step (int): Scroll step size (unused but kept for compatibility)
        scroll_pause (float): Pause between scrolls (unused but kept for compatibility)
        scroll_selector (str): CSS selector for scrollable element
        customJS (str): Custom JavaScript to execute
        waitUntil (tuple, optional): Element to wait for after clicks
        max_wait_time (int): Maximum wait time for elements
        
    """
    
    try:
        # Navigate to URL with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(url)
                driver.refresh()  # fixes most page not loading problems
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to load URL after {max_retries} attempts: {e}")
                time.sleep(2)
        
        # Disable animations for consistent screenshots
        driver.execute_script("""
            // Instant animations
            var style = document.createElement('style');
            style.innerHTML = '* {animation-duration: 0s !important; animation-delay: 0s !important; transition-duration: 0s !important; transition-delay: 0s !important;}';
            document.head.appendChild(style);
        """)
        
        # Execute custom JavaScript if provided
        if customJS:
            try:
                driver.execute_script(customJS)
            except Exception as e:
                print(f"Error executing custom JS: {e}")
        
        # Hide scrollbars for cleaner screenshots
        if scroll_selector != 'window':
            try:
                # Fixed CSS injection with proper escaping
                driver.execute_script(f"""
                    var style = document.createElement('style');
                    style.innerHTML = '{scroll_selector}::-webkit-scrollbar {{ scrollbar-width: none; -ms-overflow-style: none; display: none; }}';
                    document.head.appendChild(style);
                """)
                scroll_EL = f"document.querySelector('{scroll_selector}')"
            except Exception as e:
                print(f"Error hiding scrollbars: {e}")
                scroll_EL = 'window'
        else:
            scroll_EL = 'window'
        
        # Handle click interactions
        if clickInfo:
            for i, click in enumerate(clickInfo):
                try:
                    # Wait for element to be present and clickable
                    element = WebDriverWait(driver, max_wait_time).until(
                        EC.element_to_be_clickable((By.XPATH, click))
                    )
                    
                    # Scroll element into view
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
                    time.sleep(0.5)  # Brief pause for scroll to complete
                    
                    # Attempt to click
                    try:
                        element.click()
                    except Exception as click_error:
                        # Fallback to JavaScript click
                        print(f"Standard click failed, using JS click: {click_error}")
                        driver.execute_script("arguments[0].click();", element)
                    
                    # Wait after click
                    time.sleep(1.5)
                    
                except TimeoutException:
                    print(f"Timeout waiting for clickable element: {click} | Page: {curPage}")
                    continue
                except Exception as e:
                    print(f"Couldn't click: {click} | Page: {curPage} | Error: {str(e)}")
                    continue
        
        # Optionally wait for additional element after clicking, if specified
        if waitUntil:
            try:
                WebDriverWait(driver, max_wait_time).until(
                    EC.presence_of_element_located(waitUntil)
                )
            except TimeoutException:
                print(f"Timeout waiting for element: {waitUntil} | Page: {curPage}")
                return
            except Exception as e:
                print(f"Error waiting for element: {waitUntil} | Error: {str(e)}")
                return

        try:
            target_element = WebDriverWait(driver, max_wait_time).until(
                EC.presence_of_element_located((By.XPATH, elXpath))
            )
            time.sleep(1)
        except TimeoutException:
            print(f"Timeout waiting for target element: {elXpath} | Page: {curPage}")
            return
        except Exception as e:
            print(f"Error waiting for target element: {elXpath} | Page: {curPage} | Error: {str(e)}")
            return


        
        # Create output directory
        path = os.path.join(downloadDIR, job_id)
        os.makedirs(path, exist_ok=True)

        if scroll_selector == 'window':
            # Take screenshot of specific element
            try:
                 # get element dimensions
                element_height = driver.execute_script(
                    "return Math.ceil(arguments[0].getBoundingClientRect().height);", target_element
                )
                element_width = driver.execute_script(
                    "return Math.ceil(arguments[0].getBoundingClientRect().width);", target_element
                )
                # add some padding so the viewport is bigger than the element
                size = driver.get_window_size()

                if size["width"]<element_width+15 or size["height"]<element_height+15:

                    PADDING = 100
                    new_height = element_height + PADDING
                    new_width = element_width + PADDING

                    # resize browser window to fit
                    try:
                        driver.set_window_size(new_width, new_height)
                    except Exception:
                        # in some headless contexts resizing might be ignored; ignore failure gracefully
                        pass

                # scroll the (now visible/larger) element into center view
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
                    target_element,
                )
                time.sleep(0.5)
            
                # Take screenshot
                png_name = os.path.join(path, f"{curPage}.png")
                target_element.screenshot(png_name)
            
                # Verify screenshot was created and has content
                if not os.path.exists(png_name) or os.path.getsize(png_name) == 0:
                    print(f"Screenshot file was not created or is empty: {png_name}") 
            
            except TimeoutException:
                print(f"Target element not found: {elXpath} | Page: {curPage}")
            except Exception as e:
                print(f"Error taking screenshot of element: {elXpath} | Page: {curPage} | Error: {str(e)}")

        else:
            driver.execute_script('let style = document.createElement("style");'+
            f'style.innerHTML = "{scroll_selector}'+'::-webkit-scrollbar{scrollbar-width: none;-ms-overflow-style: none; display: none; }";'+
            'document.head.appendChild(style);')
            scroll_EL = f"document.querySelector('{scroll_selector}')"
            viewport_height = driver.execute_script(f"return {scroll_EL}.getBoundingClientRect().height;")
            total_width = driver.execute_script("return arguments[0].scrollWidth;", target_element)


            slices = []
            y = 0
            part_index = 1
            prev_end_crop = viewport_height - scroll_step
            stop = False


            try:
                driver.execute_script(f"{scroll_EL}.scrollTop = 0;")
            except Exception as e:
                print(f"[Error] Failed to scroll to top: {e}")
                return False

            while not stop:
                try:
                    if customJS:
                        driver.execute_script(customJS)
                except Exception as e:
                    print(f"[Warning] Custom JS failed during scroll: {e}")

                try:
                    prev_y = driver.execute_script(f"return {scroll_EL}.scrollTop;")
                    driver.execute_script(f"{scroll_EL}.scrollTop = {y};")
                    time.sleep(scroll_pause)
                    y = driver.execute_script(f"return {scroll_EL}.scrollTop;")

                    screenshot_filename = os.path.join(path, 'slice', f"page_{curPage}_slice_{part_index}.png")
                    target_element.screenshot(screenshot_filename)
                    img = Image.open(screenshot_filename)

                    # Crop image
                    if part_index == 1:
                        start_crop = 0
                        end_crop = img.height - scroll_step
                    elif y - prev_y == 0:
                        stop = True
                        start_crop = end_crop - (y - prev_y)
                        end_crop = img.height
                    else:
                        start_crop = prev_end_crop - y
                        end_crop = img.height - scroll_step

                    slice_img = img.crop((0, start_crop, total_width, end_crop))

                    if part_index != 1 and start_crop + y != prev_end_crop:
                        slice_img = img.crop((0, prev_end_crop - y, total_width, end_crop))

                    prev_end_crop = end_crop + y
                    slices.append(slice_img)
                    os.remove(screenshot_filename)

                    if not stop:
                        y += scroll_step
                    part_index += 1

                except Exception as e:
                    print(f"[Error] Screenshot scroll iteration failed: {e}")
                    return False

            # Stitch images and save PNG
            try:
                final_image = stitch_PNG_slices_vertically(slices)
                png_name = os.path.join(path, f"{curPage}.png")
                final_image.save(png_name)
            except Exception as e:
                print(f"[Error] Failed to stitch and save final PNG: {e}")
                return False
            

        # Convert to PDF
        pdf_name = os.path.join(path, f"{curPage}.pdf")
        png_to_pdf(png_name, pdf_name)
            
        # Verify PDF was created
        if not os.path.exists(pdf_name) or os.path.getsize(pdf_name) == 0:
            print(f"PDF file was not created or is empty: {pdf_name}")
            
        # Clean up PNG file
        try:
            os.remove(png_name)
        except Exception as e:
            print(f"Warning: Could not remove PNG file {png_name}: {e}")

    except Exception as e:
        print(f"Unexpected error in screenShotOfElement | Page: {curPage} | Error: {str(e)}")

def duplicatePage(job_id, newPageNum, pageKey, curRes, timeout=10):
    """
    Duplicates the PDF for a given page number in the job's directory.

    Args:
        job_id (str): The job identifier.
        newPageNum (int): The new page number to copy to.
        ogPageNum (int): The original page number to copy from.
        timeout (int): Time in seconds to wait for the source file to appear.

    Returns:
        bool: True if duplication succeeded, False otherwise.
    """
    path = os.path.join(downloadDIR, job_id)
    while jobs[job_id][pageKey][1] != curRes:
        time.sleep(0.2)  # Check every 200ms

    ogPageNum = jobs[job_id][pageKey][0]
    pdf_src = os.path.join(path, f"{ogPageNum}.pdf")
    pdf_dst = os.path.join(path, f"{newPageNum}.pdf")

    start_time = time.time()
    while not os.path.exists(pdf_src):
        if time.time() - start_time > timeout:
            print(f"[duplicatePage] Timeout: Source file not found: {pdf_src}")
            return False
        time.sleep(0.2)  # Check every 200ms

    try:
        shutil.copyfile(pdf_src, pdf_dst)
        return True
    except Exception as e:
        print(f"[duplicatePage] Error duplicating page {ogPageNum} to {newPageNum}: {e}")
        return False

def scan_site(site, siteName, job_id):

    # Run spider
    if jobs[job_id]['username']:
        run_spider(site, jobs[job_id]['username'], jobs[job_id]['password'])
    else:
        run_spider(site)

    urls = spider_results.get('urls', []) or []
    if jobs[job_id]['username']:
        urls = [
            u.replace('https://', f'https://{jobs[job_id]["username"]}:{jobs[job_id]["password"]}@')
            for u in urls if u not in excludedURLS
        ]
    else:
        urls = [u for u in urls if u not in excludedURLS]

    original_count = len(urls)
    if jobs[job_id]['res'] == 'both':
        urls = urls + urls  # desktop + mobile

    jobs[job_id]["total_pages"] = len(urls)
    jobs[job_id]["urls"] = urls
    jobs[job_id]['midpoint'] = original_count
    updateProgressFile(job_id)

    path = os.path.join(downloadDIR, job_id)
    os.makedirs(path, exist_ok=True)

    # Filename
    date = datetime.now().strftime("%d%b%Y")
    res_part = 'desktop_and_mobile' if jobs[job_id]['res'] == 'both' else jobs[job_id]['res']
    pdf_filename = f"{siteName}_full_{jobs[job_id]['env']}_{res_part}_site_{date}.pdf"

    def updatePageProgress():
        while True:
            pdf_files = [f for f in get_files(path) if f.lower().endswith(".pdf")]
            jobs[job_id]["current_page"] = len(pdf_files)
            updateProgressFile(job_id)
            if len(pdf_files) >= jobs[job_id]["total_pages"]:
                break
            time.sleep(1)

    progress_thread = Thread(target=updatePageProgress, daemon=True)
    progress_thread.start()

    all_threads = [progress_thread]
    all_threads = []

    def subProcess(i, url, res_type):
        if jobs[job_id]["done"] == False:
            driver = None
            try:
                with semaphore:
                    driver = driverSetUp(res_type)
                    clean_url = url.replace(f'{jobs[job_id]["username"]}:{jobs[job_id]["password"]}@', '')

                    if ('media' not in url and 'distributors' not in url and 'pdf' not in url):
                        jobs[job_id]["status"] = f"Scanning: {clean_url}"
                        updateProgressFile(job_id)
                        takeScreenShot(job_id,  i + 1, driver, url, siteName, **beforeSceenChecks(i + 1, siteName, url, job_id))
            except Exception as e:
                print(f"[Thread {i}] Error: {e}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        print(f"[Thread {i}] Error quitting driver: {e}")

    # --- Main logic ---

    main_threads = []
    numPageCounter = 0
    urls = jobs[job_id]["urls"]

    for urlCounter, url in enumerate(urls):
        res_type = jobs[job_id]['res']

        if res_type == 'both':
            res_type = 'desktop' if numPageCounter < jobs[job_id]['midpoint'] else 'mobile'

        t = Thread(target=subProcess, args=(numPageCounter, url, res_type), daemon=True)
        main_threads.append(t)
        t.start()
        numPageCounter += 1

        new_threads = afterScreenChecks(job_id, numPageCounter, url)
        if new_threads:
            for x in new_threads:
                main_threads.append(x)
                x.start()
            numPageCounter += len(new_threads)

    for t in main_threads:
        t.join()

    jobs[job_id]["status"] = "Stitching Pages together"
    updateProgressFile(job_id)

    files = get_files(path)
    merged_pdf_path = os.path.join(path, f"{jobs[job_id]['total_pages'] + 1}.pdf")

    merge_pdfs(files, merged_pdf_path, job_id)

    final_path = os.path.join(path, pdf_filename)
    os.rename(merged_pdf_path, final_path)

    jobs[job_id]["done"] = True
    jobs[job_id]["status"] = "Completed"
    jobs[job_id]['fileName'] = f"{job_id}/{pdf_filename}"
    jobs[job_id]['showProgress'] = 'd-none'  # hides progress bar
    updateProgressFile(job_id)

def updateProgressFile(job_id):
    with open(os.path.join( os.path.dirname(BASE_DIR),"json",f"{job_id}.json"), "w") as json_file:
        json.dump(jobs, json_file, indent=4)
        

def folderCleanUp():
    path = os.path.join(os.path.dirname(BASE_DIR), "json")
    jsonLst = get_files(path)
    idsTOremove = []
    for job_id in jsonLst:  # make sure get_files returns filenames like 'uuid.json'
        file_path = os.path.join(path, job_id)
        try:
            with open(file_path, "r") as json_file:
                data = json.load(json_file)
            # Assuming the job ID is the key in the JSON root object:
            job_key = list(data.keys())[0]  # get the job id key inside JSON

            job_info = data[job_key]
            job_start_time_str = job_info.get("jobStartTime")

            if job_start_time_str:
                job_start_time = datetime.strptime(job_start_time_str, "%Y-%m-%d %H:%M:%S.%f")
                if datetime.now() - job_start_time > timedelta(days=1) or job_info.get("done"):
                    os.remove(file_path)
                    idsTOremove.append(job_id)

                    print(f"removed job_id: {job_id}")
        except Exception as e:
            print(f"Failed to process {job_id}: {e}")
    

    for i in range(len(jsonLst[::-1])):
        if jsonLst[::-1][i] in idsTOremove:
            del jsonLst[::-1][i]

    for i in [f for f in os.listdir(downloadDIR)]:
        if i+'.json' not in jsonLst:

            download_path = os.path.join(downloadDIR, i)
            if os.path.exists(download_path):
                shutil.rmtree(download_path)
        
#clear conosole
os.system('cls' if os.name == 'nt' else 'clear')

# folderCleanUp()
# input order
#JobId site siteURL env res

if len(sys.argv) == 1:
    #test values
    job_id = 'test_job_123'
    site = 'Example'
    siteUrl = "https://example.com/"
    env ='p'  # 's' for staging, 'p' for production
    res = 'desktop'  # 'desktop', 'mobile', or 'both'
    userName = None
    password = None
else:

    job_id = sys.argv[1]
    site = sys.argv[2]
    siteUrl = sys.argv[3]
    env = sys.argv[4]  # 's' for staging, 'p' for production
    res = sys.argv[5]  # 'desktop', 'mobile', or 'both'
    if len(sys.argv) > 6:
        userName = sys.argv[6]
        password = sys.argv[7]
    else:
        userName = None
        password = None

print(type(userName),password)

jobs[job_id] = {
        "current_page": 0,
        "done": False,
        "status": "Queued...",
        "fileName": None,
        "showProgress": "",
        "dowloaded": False,
        "total_pages": "Searching...",
        "jobStartTime": str(datetime.now()),
        "res": res,
        'env': env,
        "siteName":site,
        "username": userName,
        "password": password,
    }
updateProgressFile(job_id)

# Create directory
path = os.path.join(downloadDIR, job_id)
if not os.path.exists(path):
    os.makedirs(path)
files = get_files(path)
for f in files:
    os.remove(os.path.join(path, f))


scan_site(siteUrl, site, job_id)  



