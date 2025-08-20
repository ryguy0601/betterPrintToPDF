from globals import *
from threading import Thread
import traceback


#selector options
ID = "id"
XPATH = "xpath"
LINK_TEXT = "link text"
PARTIAL_LINK_TEXT = "partial link text"
NAME = "name"
TAG_NAME = "tag name"
CLASS_NAME = "class name"
CSS_SELECTOR = "css selector"

sites = {#s for stage p for prod, the order of this list affects the order of the dropdown
    # change these defaults to whatever sites you want to include
    "Example1": {
        's':"https://example1.stage.com/",#stage
        'p':'https://example1.com/'},#production
    "Example2": {
        's':"https://example2.stage.com/",
        'p':'https://example2.com/'},
}

# excludedURLS = ['https://example.example.com/']  
excludedURLS = []  

def beforeSceenChecks(i, siteName, url, job_id):
    """
    Returns custom arguments for site-specific pre-screenshot logic.

    Args:
        i (int): Current page index or step in the screenshot process.
        siteName (str): Name of the site being processed.
        url (str): URL of the page being processed.
        job_id (str): Identifier for the current job.

    Returns:
        dict: Dictionary of arguments for screenshot logic.

    The returned dictionary may include the following options (with their defaults) All optional:

        - clickInfo: list of element xPaths to click (default: None)
        - scroll_step: number of pixels to scroll per step (default: 200)
        - scroll_pause: pause time in seconds between scroll steps (default: 0.00)
        - scroll_selector: CSS selector for scrollable element, default is whole page ('window')
        - customJS: custom JavaScript to execute (default: '')
        - waitUntil: tuple of (selector option(listed at top of page), selector) to wait for after clicks (default: None)
        - waitTime: wait time after page load Ex: for animations or transitions (default:0)
    """
    """
    info about job id;
    jobs[job_id]['midpoint'] used for when you want to get the page number that seperates the desktop and mobile when desktop and mobile is selected in the interface

    """

    args = {}

    if siteName == "Example1": #apply to every page of the site
        args['waitTime']=3 #waits 3 seconds after the page has loaded before taking the screenshot, use cases waiting for an animation to load
        args['clickInfo'] = [
            '*close Cookie xpath here*',
            '*close popup xpath here*',
        ]

    elif siteName == "Example2" and i == 1: #apply to the first page of the site, if desktop and mobile is selected, it would only apply on the first page of the desktop
        #pick any of the selector options listed at teh top of the page
        args['waitUntil'] = (CSS_SELECTOR, ".className"),#waits until this element is loaded then the program starts (intended to select only 1 element)
        args['clickInfo'] = [
            '*close Cookie xpath here*',
            '*close popup xpath here*',
        ]
    elif siteName == "Example2" and url == 'https://example2.stage.com/page1': #apply to only this page would work for both desktop and mobile
        args['clickInfo'] = [
            '*close Cookie xpath here*',
            '*close popup xpath here*',
        ]

    else:
        #anything you want to apply to all pages of every site put here
        args['clickInfo'] = ['xpath Here']

    return args


def afterScreenChecks(job_id, curPage, url):
    """
    Performs additional screenshot operations for specific sites/web pages after initial screenshot.

    Args:
        job_id (str): Job identifier.
        curPage (int): Current page number.
        url (str): The current URL being processed.

    Returns:
        list: List of thread objects that need to be joined by caller.
    """
    from main import screenShotOfElement, takeScreenShot, driverSetUp, duplicatePage, updateProgressFile#(DONT DELETE)

    siteName = jobs[job_id]['siteName']#(DONT DELETE)
    functions = {'name': [], 'args': [], 'kwargs': []}#(DONT DELETE)
    
    # Determine resolution based on job configuration (DONT DELETE)
    if jobs[job_id]['res'] == 'both' and curPage - 1 >= jobs[job_id]['midpoint']:
        res = 'mobile'
    else:
        res = 'mobile' if jobs[job_id]['res'] == 'mobile' else 'desktop'
    

    driver = None#(DONT DELETE) for if u need to check for something on the page before scaning it using selenium logic

    # Start custom code
    if siteName == "Example1":
        #this would incert a page after every page scaned for this one site
        jobs[job_id]["status"] = 'Running after-screen logic for Example1'#update status for web interface
        functions['name'].append(takeScreenShot)#this function takes a screenshot of the whole page
        functions['args'].append((url))#url recomend using url var for most cases
        functions['kwargs'].append({
            'clickInfo': [
                'xpath here',
                'xpath here',
                'xpath here',
            ],
            'scroll_selector': '#elementIDhere'#select what will be scrolled for the screenshot (good for popups)
        })

    elif siteName == 'Example2':
        jobs[job_id]["status"] = 'Scanning: dropdowns and other hidden text'

        if res == 'desktop':#only when in desktop mode if you want only mobile replace with 'mobile', if for both get rid of the if statement entirely
            if url == 'https://example2.com/' or url == 'https://example2.com/page1':#only for these pages
                # 1st and 2nd screenshot
                functions['name'].append(screenShotOfElement)#takes screenshot of specific element when given the xpath
                functions['args'].append((url, 'xpath here'))
                functions['kwargs'].append({
                    'clickInfo': [
                        'xpath here',
                        'xpath here',
                    ],
                    'customJS': f"alert('Custom JS for {url}');"#runs whatever javascript code you want every time it takes a screenshot(it takes several per page a stiches them together)
                })


        if url == 'https://example2.com/page1':
            driver = driverSetUp(res)#opens chrome with current dimensions
            driver.get(url)#goes to page
            driver.refresh()#refreshes the page(i find it helps a lot  with loading issues)
            #any custom logic you want
            #for example you need to take a screen shot of every item in a carousel
            carousel_items = driver.find_elements(XPATH, '//*[@id="carousel-id"]/div')
            for item in carousel_items:#this code will not work it is just an example
                functions['name'].append(screenShotOfElement)
                functions['args'].append((url, item))
                functions['kwargs'].append({
                    'clickInfo': [
                        'xpath here',
                        'xpath here',
                    ],
                    'customJS': f"alert('Custom JS for {url}');"
                })


    

        if driver:#(DONT DELETE)
            driver.quit()#(DONT DELETE)

    else:#(DONT DELETE)
        return None#(DONT DELETE)

    # Create drivers and insert into args
    functions['drivers'] = [driverSetUp(res) for _ in range(len(functions['name']))]
    for i in range(len(functions['args'])):
        args_list = list(functions['args'][i])
        args_list.insert(0, job_id)     # Insert job_id at index 0
        args_list.insert(1, curPage + i + 1)              # Insert current page at index 1
        if functions['name'][i] != duplicatePage:
            args_list.insert(2, functions['drivers'][i])     # Insert driver at index 2
        args_list.insert(4, siteName)
        functions['args'][i] = tuple(args_list)
    
            
    # Update job metadata (DONT DELETE)
    jobs[job_id]["total_pages"] += len(functions['args'])
    jobs[job_id]['midpoint'] += len(functions['args'])
    updateProgressFile(job_id)#(DONT DELETE)

    threads = []#(DONT DELETE)

    #(DONT DELETE)
    def run_func_in_thread(i):
        print("test")
        driver_to_close = None
        try:
            with semaphore:
                func = functions['name'][i]
                args = functions['args'][i]
                kwargs = functions['kwargs'][i]
                driver_to_close = functions['drivers'][i]

                func(*args, **kwargs)

                if job_id in jobs:
                    jobs[job_id]["current_page"] += 1
                    updateProgressFile(job_id)

        except Exception as e:
            print(f"[afterScreenChecks Thread {i}] Error: {e}")
            print(f"[afterScreenChecks Thread {i}] Traceback: {traceback.format_exc()}")

        finally:
            if driver_to_close:
                try:
                    driver_to_close.quit()
                    print(f"[afterScreenChecks Thread {i}] Driver closed successfully")
                except Exception as e:
                    print(f"[afterScreenChecks Thread {i}] Error closing driver: {e}")

    # Spawn and return threads (DONT DELETE)
    for i in range(len(functions['name'])):
        t = Thread(target=run_func_in_thread, args=(i,), daemon=True)
        threads.append(t)

    return threads  #(DONT DELETE) Caller must .start() and .join() the threads
