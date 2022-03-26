# source: https://medium.com/geekculture/scraping-images-using-selenium-f35fab26b122

# Importing libraries
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os
# from pyvirtualdisplay import Display


# Selenium setup
def get_selenium():

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    ###########################################
    # display = Display(visible=0, size=(800, 600))
    # display.start()
    # options = Options()
    # options.add_argument("disable-infobars")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--headless")
    # chrome_options = options
    # options.add_argument("window-size=1400,600")

    # For making the app independent of chrome driver files
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s, chrome_options=chrome_options)
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver.maximize_window()
    # time.sleep(3)

    # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    driver.delete_all_cookies()
    # time.sleep(3)
    # display.stop()
    return driver

# We need to make sure that each time we load the page, it goes to the end of the webpage.

def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

        # build the google query

    # URL
    url = f"https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={query}&oq={query}&gs_l=img"

    # load the page
    wd.get(url)

    image_urls = set()
    image_count = 0
    results_start = 0

    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements(by=By.CSS_SELECTOR, value="img.Q4LuWd")
        num_results = len(thumbnail_results)

        print(f"Found: {num_results} search results. Extracting links from {results_start}:{num_results}")

        for img in thumbnail_results[results_start:num_results]:
            # Try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                # time.sleep(sleep_between_interactions)
            except Exception:
                continue

            # Extract image urls
            actual_imgs = wd.find_elements(by=By.CSS_SELECTOR, value='img.n3VNCb')
            for actual_img in actual_imgs:
                if actual_img.get_attribute("src") and "http" in actual_img.get_attribute("src"):
                    image_urls.add(actual_img.get_attribute("src"))

            image_count = len(image_urls)

            if image_count >= max_links_to_fetch:
                print(f"Found: {image_count} image links, done!")
                break
            else:
                print("Found:", image_count, "image links, looking for more...")
                # time.sleep(30)
                load_more_button = wd.find_elements(by=By.CSS_SELECTOR, value=".mye4qd")

                if load_more_button:
                    wd.execute_script("document.querySelector('.mye4qd').click();")

            # Move the result starting point furthur down
            results_start = len(thumbnail_results)

        return image_urls

    #     print(img)
# Fix infinite scrolling
# selenium = get_selenium()

# selenium.get("")