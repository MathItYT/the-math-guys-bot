from selenium import webdriver
from selenium.webdriver.common.by import By
from base64 import b64decode
from selenium.webdriver.common.actions.action_builder import ActionBuilder

import time


browser = webdriver.Chrome()


def main():
    browser.get("https://amctrivial.com/")
    browser.fullscreen_window()
    time.sleep(1)
    elem = browser.find_element(By.ID, "problem-batch")
    elem.click()

    action = ActionBuilder(browser)
    action.pointer_action.move_to_location(1304, 520)
    action.pointer_action.click()
    action.perform()

    time.sleep(3)

    for i in range(1, 31):
        pdf = browser.print_page()
        pdf_bytes = b64decode(pdf)

        with open(f"problems/set{i}.pdf", "wb") as f:
            f.write(pdf_bytes)

        action.pointer_action.move_to_location(1240, 575)
        action.pointer_action.click()
        action.perform()

        time.sleep(3)


if __name__ == "__main__":
    main()
