import os
import time
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.excel_util import list_files_in_output
from utils.selenium_util import SeleniumUtil


def login(
        _browser: SeleniumUtil,
        isHaveItem: bool = False,
) -> None:
    _browser.get(
        "https://www.playerauctions.com/wow-classic-gold/?Serverid=13563&Quantity=6000&PageIndex=1"
    )

    ## start: accept cookies
    try:
        cookies_tag = _browser.driver.find_element(By.CSS_SELECTOR, ".btn.chooese-btn.btn-shadow.allow-all.accept-btn-ok")
        cookies_tag.click()
    except Exception:
        print("No cookies tag")
    ## end: accept cookies

    _browser.click_by_inner_text("LOG IN")

    username_tag = _browser.driver.find_element(By.ID, "username")
    username_tag.send_keys(os.getenv("PA_USERNAME"))

    pass_tag = _browser.driver.find_element(By.ID, "password")
    pass_tag.send_keys(os.getenv("PA_PASSWORD"))

    inner_text = " LOG IN "  # Replace with the desired text
    _browser.click_by_inner_text(inner_text)
    sleep(3)
    while True:
        try:
            print(
                _browser.driver.execute_script(
                    """
            var response = grecaptcha.getResponse();
            response.length
        """
                )
            )
            time.sleep(3)
        except Exception:
            break
    ### upload currency file
    for file in list_files_in_output('storage/output/currency'):
        sendCurrencyFile(_browser, file)
        print(f"Uploaded")
        time.sleep(30)

    if isHaveItem:
        ### upload item file
        for file in list_files_in_output('storage/output/item'):
            sendItemFile(_browser, file)
            print(f"Uploaded")
            time.sleep(30)

    _browser.close()


def sendCurrencyFile(_browser: SeleniumUtil, path: str) -> None:
    _browser.get(
        "https://me.playerauctions.com/member/batchoffer/?menutype=offer&menusubtype=currencybulkoffertool"
    )

    file_path = os.path.abspath(path)

    file_input = WebDriverWait(_browser.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    # Upload the file using the absolute path
    file_input.send_keys(file_path)

    # Optionally, you can click the "BROWSE FILES" button if needed
    browse_button = _browser.driver.find_element(By.CSS_SELECTOR, "input.ant-checkbox-input")
    browse_button.click()
    _browser.click_by_inner_text("UPLOAD")


def sendItemFile(_browser: SeleniumUtil, path: str) -> None:
    _browser.get(
        "https://me.playerauctions.com/member/itemsbulkupload/?menutype=offer&menusubtype=itembulkoffertool"
    )

    file_path = os.path.abspath(path)

    file_input = WebDriverWait(_browser.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    # Upload the file using the absolute path
    file_input.send_keys(file_path)

    # Optionally, you can click the "BROWSE FILES" button if needed
    browse_button = _browser.driver.find_element(By.CSS_SELECTOR, "input.ant-checkbox-input")
    browse_button.click()
    _browser.click_by_inner_text("UPLOAD")


if __name__ == "__main__":
    browser = SeleniumUtil(mode=1)
    login(browser)
