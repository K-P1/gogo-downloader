from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import logging

class WebDriverManager:
    def __init__(self, firefox_binary_path, geckodriver_path):
        self.firefox_binary_path = firefox_binary_path
        self.geckodriver_path = geckodriver_path
        self.driver = None

    def __enter__(self):
        logging.info("Initializing WebDriver")
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.binary_location = self.firefox_binary_path
        service = FirefoxService(executable_path=self.geckodriver_path)
        self.driver = webdriver.Firefox(service=service, options=options)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            logging.info("Closing WebDriver")
            self.driver.quit()
            self.driver = None