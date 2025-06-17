from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

def take_fullpage_screenshot(url, output_file='screenshot.png'):
    """
    Takes a full-page screenshot of the given URL using Selenium WebDriver.
    :param url:
    :param output_file:
    :return:
    """
    options = Options()
    options.add_argument("--headless=new")  # new headless mode
    options.add_argument("--window-size=1920,1080")  # initial window size
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    # Give the page some time to load
    time.sleep(2)
    # Calculate full height of page
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    # Resize the window to capture the full page
    driver.set_window_size(1920, scroll_height)
    # Take screenshot
    driver.save_screenshot(output_file)
    driver.quit()
    print(f"Screenshot saved to {output_file}")


if __name__ == '__main__':
    url = "https://www.nokillmag.com/articles/how-to-step-up-your-style-game-with-modular-fashion-5-brands-to-know/"  # Replace with the URL you want to capture
    output_file = "fullpage_screenshot.png"
    take_fullpage_screenshot(url, output_file)
