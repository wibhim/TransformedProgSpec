#To test Selenium

# from selenium import webdriver
# driver = webdriver.Chrome()  # Or webdriver.Firefox(), depending on your browser choice
# driver.get("https://www.example.com")
# print(driver.title)
# driver.quit()

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Set up the Chrome WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# URL of the web page
url = "https://github.com/Decodo/Decodo"

# Open the web page
driver.get(url)

# Get the page HTML source
page_source = driver.page_source

# Parse the HTML using BeautifulSoup
soup = BeautifulSoup(page_source, "html.parser")

# Find the element with the specified class name
about_element = soup.find(class_="f4 my-3")
about_text = about_element.text.strip()

# Print the About section content
print(about_text)

# Close the browser
driver.quit()