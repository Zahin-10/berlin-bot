import time
import os
import logging
from platform import system

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

from your_info import *

system = system()

logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)

class WebDriver:
    def __init__(self):
        self._driver: uc.Chrome
        self._implicit_wait_time = 600

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")
        # some stuff that prevents us from being locked out
        self._driver = uc.Chrome(headless=False,use_subprocess=False)
        self._driver.implicitly_wait(self._implicit_wait_time) # seconds
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self._driver.quit()

class BerlinBot:
    def __init__(self):
        self.wait_time = 5
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""
        self._error_message2 = """Sitzungsende"""

    @staticmethod
    def enter_start_page(driver: uc.Chrome):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen/wizardng?sprachauswahl=de")
        #driver.find_element(By.XPATH, '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a').get_attribute('value')
        driver.find_element(By.XPATH, '//*[@id="xi-txt-1"]/h1/span').get_attribute('value')
        time.sleep(5)

    @staticmethod
    def tick_off_some_bullshit(driver: uc.Chrome):
        logging.info("Ticking off agreement")
        driver.find_element(By.XPATH, '//*[@id="xi-div-1"]/div[4]/label[2]/p').click()
        time.sleep(1)
        driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
        #WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID, 'xi-sel-400'))
        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID, 'xi-sel-400')))
        time.sleep(5)

    @staticmethod
    def enter_form(driver: uc.Chrome):
        logging.info("Fill out form")
        # select china
        s = Select(driver.find_element(By.ID, 'xi-sel-400'))
        s.select_by_visible_text(country)
        logging.info("selected Country")
        time.sleep(2)

        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID, 'xi-sel-422')))
        # eine person
        s = Select(driver.find_element(By.ID, 'xi-sel-422'))
        s.select_by_visible_text("eine Person")
        logging.info("selected person")   
        time.sleep(3)
        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID, 'xi-sel-427')))
        # no family
        s = Select(driver.find_element(By.ID, 'xi-sel-427'))
        s.select_by_visible_text("nein")
        logging.info("selected family")
        time.sleep(3)

        # extend stay
        # wait until element is present
        e1= WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, residence_option))
        )
        e1.click()

        time.sleep(3)

        # click on study group
        #driver.find_element(By.CSS_SELECTOR, '#inner-460-0-2 > div > div.ozg-accordion.accordion-460-0-2-3.level2 > label > p').click()
        if residence_option == "//p[contains(.,'Aufenthaltstitel - verlängern')]" or residence_option == "//p[contains(.,'Aufenthaltstitel - beantragen')]":
            e1 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, group_option))
            )
            e1.click()
        time.sleep(3)

        # b/c of stufy
        e1 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, reason_option))
        )
        e1.click()
        #driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div[2]/form/div[2]/div/div[2]/div[8]/div[2]/div[2]/div[1]/fieldset/div[8]/div[1]/div[1]/div[1]/div[9]/div/div[2]/div/div[5]/label').click()
        time.sleep(3)

        if residence_option == "//p[contains(.,'Duldung - verlängern')]" or residence_option == "//p[contains(.,' Aufenthaltsgestattung (Asyl) - verlängern')]":
            input_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'nnachnamezmsVal'))
            )
            input_box.send_keys(last_name)
            actions = ActionChains(driver)

            # Move the mouse 50 pixels down from the input box and click
            actions.move_to_element_with_offset(input_box, 0, 50).click().perform()
            time.sleep(4)



        # submit form
        driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
        time.sleep(10)


    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            self._play_sound_osx(self._sound_file)
            time.sleep(15)
        
        # todo play something and block the browser


    def run_once(self):
        with WebDriver() as driver:
            try:

                self.enter_start_page(driver)
                self.tick_off_some_bullshit(driver)
                self.enter_form(driver)

                # retry submit
                while True:
                    if self._error_message2 in driver.page_source:
                        self._play_sound_osx(self._sound_file)
                        self.enter_start_page(driver)
                        self.tick_off_some_bullshit(driver)
                        self.enter_form(driver)
                    if not self._error_message in driver.page_source:
                        self._success()
                    logging.info("Retry submitting form")
                    driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
                    time.sleep(self.wait_time)
            except Exception as e:
                    logging.info(driver.get_log('driver'))
                    logging.info(driver.get_log('browser'))
                    print("Loading took too much time!")
    def run_loop(self):
        # play sound to check if it works
        self._play_sound_osx(self._sound_file)
        while True:
            logging.info("One more round")
            self.run_once()
            time.sleep(self.wait_time)

    # stolen from https://github.com/JaDogg/pydoro/blob/develop/pydoro/pydoro_core/sound.py
    @staticmethod
    def _play_sound_osx(sound, block=True):
        """
        Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
        OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
        Probably works on OS X 10.5 and newer. Probably works with all versions of
        Python.
        Inspired by (but not copied from) Aaron's Stack Overflow answer here:
        http://stackoverflow.com/a/34568298/901641
        I never would have tried using AppKit.NSSound without seeing his code.
        """
        from AppKit import NSSound
        from Foundation import NSURL
        from time import sleep

        logging.info("Play sound")
        if "://" not in sound:
            if not sound.startswith("/"):
                from os import getcwd

                sound = getcwd() + "/" + sound
            sound = "file://" + sound
        url = NSURL.URLWithString_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not nssound:
            raise IOError("Unable to load sound named: " + sound)
        nssound.play()

        if block:
            sleep(nssound.duration())

if __name__ == "__main__":
    BerlinBot().run_loop()
