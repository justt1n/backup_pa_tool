import os

from dotenv import load_dotenv

import constants
from app.login import login
from app.process import run, get_row_run_index, is_change_price, calculate_price_change
from main import read_file_with_encoding
from model.payload import Row
from utils.biji_extract import bij_lowest_price
from utils.ggsheet import GSheet, Sheet
from utils.pa_extract import extract_offer_items
from utils.selenium_util import SeleniumUtil


def test():
    run()

def test_login():
    browser = SeleniumUtil()
    login(browser)

def test_run_bij():
    gsheet = GSheet()
    browser = SeleniumUtil()
    BIJ_HOST_DATA = read_file_with_encoding(constants.DATA_PATH, encoding='utf-8')
    sheet = Sheet.from_sheet_id(
        gsheet=gsheet,
        sheet_id=os.getenv("SPREADSHEET_ID"),  # type: ignore
    )
    worksheet = sheet.open_worksheet(os.getenv("SHEET_NAME"))  # type: ignore
    row_indexes = get_row_run_index(worksheet=worksheet)
    for index in row_indexes:
        print(f"Row: {index}")
        row = Row.from_row_index(worksheet, index)
        bij_lowest_price(BIJ_HOST_DATA, browser, row.bij)


BIJ_HOST_DATA = None

if __name__ == "__main__":
    load_dotenv('settings.env')
    test_run_bij()