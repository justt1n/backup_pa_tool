from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing import Annotated, cast

from decorator.time_execution import time_execution
from utils.ggsheet import GSheet, Sheet
from utils.google_api import StockManager


class BaseGSheetModel(BaseModel):
    row_index: int | None = None

    @classmethod
    def fields_exclude_row_index(
        cls,
    ) -> dict[str, FieldInfo]:
        dic: dict[str, FieldInfo] = {}
        for k, v in cls.model_fields.items():
            if k != "row_index":
                dic[k] = v
        return dic


class Product(BaseGSheetModel):
    CHECK: Annotated[int, "B"]
    Product_name: Annotated[str, "C"]
    Note: Annotated[str | None, "D"] = None
    Last_Update: Annotated[str | None, "E"] = None
    Product_link: Annotated[str, "F"]
    PRODUCT_COMPARE: Annotated[str, "G"]
    TITLE: Annotated[str | None, "H"] = ''
    DESCRIPTION: Annotated[str | None, "I"] = ''
    DURATION: Annotated[str | None, "J"] = ''
    DONGIAGIAM_MIN: Annotated[float, "K"]
    DONGIAGIAM_MAX: Annotated[float, "L"]
    DONGIA_LAMTRON: Annotated[int, "M"]
    EXCLUDE_ADS: Annotated[int, "N"]
    DELIVERY_TIME: Annotated[str, "O"]
    FEEDBACK: Annotated[int, "P"]
    MIN_UNIT: Annotated[int, "Q"]
    MINSTOCK: Annotated[int, "R"]
    IDSHEET_MIN: Annotated[str, "S"]
    SHEET_MIN: Annotated[str, "T"]
    CELL_MIN: Annotated[str, "U"]
    IDSHEET_MIN2: Annotated[str, "V"]
    SHEET_MIN2: Annotated[str, "W"]
    CELL_MIN2: Annotated[str, "X"]
    DELIVERY0: Annotated[str, "Y"]
    DELIVERY1: Annotated[str, "Z"]
    IDSHEET_MAX: Annotated[str, "AA"]
    SHEET_MAX: Annotated[str, "AB"]
    CELL_MAX: Annotated[str, "AC"]
    IDSHEET_MAX2: Annotated[str, "AD"]
    SHEET_MAX2: Annotated[str, "AE"]
    CELL_MAX2: Annotated[str, "AF"]
    IDSHEET_MIN_STOCKFAKE: Annotated[str, "CO"]
    SHEET_MIN_STOCKFAKE: Annotated[str, "CP"]
    CELL_MIN_STOCKFAKE: Annotated[str, "CQ"]
    IDSHEET_MAX_STOCKFAKE: Annotated[str, "CR"]
    SHEET_MAX_STOCKFAKE: Annotated[str, "CS"]
    CELL_MAX_STOCKFAKE: Annotated[str, "CT"]

    def min_price_stock_1(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet_manager = StockManager(self.IDSHEET_MIN)
        cell_value = sheet_manager.get_stock(f"'{self.SHEET_MIN}'!{self.CELL_MIN}")
        # sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MIN)
        # worksheet = sheet.open_worksheet(self.SHEET_MIN)
        # cell_value = worksheet.batch_get([self.CELL_MIN])[0]

        return float(cell_value)  # type: ignore

    def max_price_stock_1(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet_manager = StockManager(self.IDSHEET_MAX)
        cell_value = sheet_manager.get_stock(f"'{self.SHEET_MAX}'!{self.CELL_MAX}")
        # sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MAX)
        # worksheet = sheet.open_worksheet(self.SHEET_MAX)
        # cell_value = worksheet.batch_get([self.CELL_MAX])[0]
        return float(cell_value)  # type: ignore

    def min_price_stock_2(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet_manager = StockManager(self.IDSHEET_MIN2)
        cell_value = sheet_manager.get_stock(f"'{self.SHEET_MIN2}'!{self.CELL_MIN2}")
        # sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MIN2)
        # worksheet = sheet.open_worksheet(self.SHEET_MIN2)
        # cell_value = worksheet.batch_get([self.CELL_MIN2])[0]
        return float(cell_value)  # type: ignore

    def max_price_stock_2(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet_manager = StockManager(self.IDSHEET_MAX2)
        cell_value = sheet_manager.get_stock(f"'{self.SHEET_MAX2}'!{self.CELL_MAX2}")
        # sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MAX2)
        # worksheet = sheet.open_worksheet(self.SHEET_MAX2)
        # cell_value = worksheet.batch_get([self.CELL_MAX2])[0]
        return float(cell_value)  # type: ignore

    def get_stock_fake_min_price(self):
        sheet_manager = StockManager(self.IDSHEET_MIN_STOCKFAKE)
        cell_value = sheet_manager.get_stock(f"'{self.SHEET_MIN_STOCKFAKE}'!{self.CELL_MIN_STOCKFAKE}")
        return float(cell_value)

    def get_stock_fake_max_price(self):
        sheet_manager = StockManager(self.IDSHEET_MAX_STOCKFAKE)
        cell_value = sheet_manager.get_stock(f"'{self.SHEET_MAX_STOCKFAKE}'!{self.CELL_MAX_STOCKFAKE}")
        return float(cell_value)


class StockInfo(BaseGSheetModel):
    IDSHEET_STOCK: Annotated[str, "AG"]
    SHEET_STOCK: Annotated[str, "AH"]
    CELL_STOCK: Annotated[str, "AI"]
    IDSHEET_STOCK2: Annotated[str, "AJ"]
    SHEET_STOCK2: Annotated[str, "AK"]
    CELL_STOCK2: Annotated[str, "AL"]
    STOCK_LIMIT: Annotated[int, "AM"]
    STOCK_LIMIT2: Annotated[int, "AN"]
    STOCK_FAKE: Annotated[int | None, "AO"] = None
    PA_IDSHEET_BLACKLIST: Annotated[str | None, "AP"] = ""
    PA_SHEET_BLACKLIST: Annotated[str | None, "AQ"] = ""
    PA_CELL_BLACKLIST: Annotated[str | None, "AR"] = ""
    _stock1: int | None = 0
    _stock2: int | None = 0

    def get_pa_blacklist(self) -> list[str]:
        blacklist = []
        try:
            sheet_manager = StockManager(self.PA_IDSHEET_BLACKLIST)
            blacklist = sheet_manager.get_multiple_str_cells(f"'{self.PA_SHEET_BLACKLIST}'!{self.PA_CELL_BLACKLIST}")
        except Exception as e:
            print("Cant get pa blacklist: ", e)
            pass
        return blacklist

    def stock_1(
        self,
        gsheet: GSheet,
    ) -> int:
        stock_mng = StockManager(self.IDSHEET_STOCK)
        stock1 = stock_mng.get_stock(f"'{self.SHEET_STOCK}'!{self.CELL_STOCK}")
        try:
            self._stock1 = stock1  # type: ignore
            return stock1  # type: ignore
        except Exception as e:
            print(e)
            raise Exception("Error getting stock 1")

    def stock_2(
        self,
        gsheet: GSheet,
    ) -> int:
        stock_mng = StockManager(self.IDSHEET_STOCK)
        stock2 = stock_mng.get_stock(f"'{self.SHEET_STOCK}'!{self.CELL_STOCK}")
        try:
            self._stock2 = stock2  # type: ignore
            return stock2  # type: ignore
        except Exception as e:
            print(e)
            raise Exception("Error getting stock 2")

    def get_stocks(self):
        if self.IDSHEET_STOCK == self.IDSHEET_STOCK2:
            stock_manager = StockManager(self.IDSHEET_STOCK)
            cell1 = f"'{self.SHEET_STOCK}'!{self.CELL_STOCK}"
            cell2 = f"'{self.SHEET_STOCK}'!{self.CELL_STOCK2}"
            stock1, stock2 = stock_manager.get_multiple_cells([cell1, cell2])
        else:
            stock_mng = StockManager(self.IDSHEET_STOCK)
            stock1 = stock_mng.get_stock(f"'{self.SHEET_STOCK}'!{self.CELL_STOCK}")
            stock_mng = StockManager(self.IDSHEET_STOCK2)
            stock2 = stock_mng.get_stock(f"'{self.SHEET_STOCK2}'!{self.CELL_STOCK2}")
        self._stock1 = stock1
        self._stock2 = stock2
        return stock1, stock2

    def cal_stock(self) -> int:
        if self._stock1 == 0 or self._stock1 < self.STOCK_LIMIT:
            if self._stock2 == 0 or self._stock2 < self.STOCK_LIMIT2:
                return self.STOCK_FAKE
            return self._stock2
        return self._stock1


class G2G(BaseGSheetModel):
    G2G_CHECK: Annotated[int, "AS"]
    G2G_PROFIT: Annotated[float, "AT"]
    G2G_PRODUCT_COMPARE: Annotated[str, "AU"]
    G2G_IDSHEET_PRICESS: Annotated[str, "AV"]
    G2G_SHEET_PRICESS: Annotated[str, "AW"]
    G2G_CELL_PRICESS: Annotated[str, "AX"]
    G2G_QUYDOIDONVI: Annotated[float, "AY"]

    def get_g2g_price(
            self
    ) -> float:
        sheet_manager = StockManager(self.G2G_IDSHEET_PRICESS)
        blacklist = sheet_manager.get_stock(f"'{self.G2G_SHEET_PRICESS}'!{self.G2G_CELL_PRICESS}")
        return blacklist


class FUN(BaseGSheetModel):
    FUN_CHECK: Annotated[int, "AZ"]
    FUN_PROFIT: Annotated[float, "BA"]
    FUN_DISCOUNTFEE: Annotated[float, "BB"]
    FUN_PRODUCT_COMPARE: Annotated[str, "BC"]
    FUN_IDSHEET_PRICESS: Annotated[str, "BD"]
    FUN_SHEET_PRICESS: Annotated[str, "BE"]
    FUN_CELL_PRICESS: Annotated[str, "BF"]
    FUN_QUYDOIDONVI: Annotated[float | None, "BG"] = None


    def get_fun_price(self) -> float:
        sheet_manager = StockManager(self.FUN_IDSHEET_PRICESS)
        blacklist = sheet_manager.get_stock(f"'{self.FUN_SHEET_PRICESS}'!{self.FUN_CELL_PRICESS}")
        return blacklist


class BIJ(BaseGSheetModel):
    BIJ_CHECK: Annotated[int, "BH"]
    BIJ_PROFIT: Annotated[float, "BI"]
    # BIJ_NAME: Annotated[str, "BG"]
    # BIJ_SERVER: Annotated[str, "BH"]
    BIJ_PRODUCT_COMPARE: Annotated[str, "BJ"]
    BIJ_IDSHEET_PRICESS: Annotated[str | None, "BK"] = None
    BIJ_SHEET_PRICESS: Annotated[str | None, "BL"] = None
    BIJ_CELL_PRICESS: Annotated[str | None, "BM"] = None
    BIJ_QUYDOIDONVI: Annotated[float | None, "BN"] = None

    def get_bij_price(self) -> float:
        sheet_manager = StockManager(self.BIJ_IDSHEET_PRICESS)
        blacklist = sheet_manager.get_stock(f"'{self.BIJ_SHEET_PRICESS}'!{self.BIJ_CELL_PRICESS}")
        return float(blacklist)


class ExtraInfor(BaseGSheetModel):
    MIN_UNIT_PER_ORDER: Annotated[int, "BO"]
    VALUE_FOR_DISCOUNT: Annotated[str | None, "BP"] = ""
    DISCOUNT: Annotated[str | None, "BQ"] = ""
    DELIVERY_GUARANTEE: Annotated[int, "BR"]
    CURRENCY_PER_UNIT: Annotated[str, "BS"]
    GAME_LIST_SHEET_ID: Annotated[str | None, "BT"] = ""
    GAME_LIST_SHEET: Annotated[str | None, "BU"] = ""
    GAME_LIST_CELLS: Annotated[str | None, "BV"] = ""

    def get_game_list(self) -> list[str]:
        sheet_manager = StockManager(self.GAME_LIST_SHEET_ID)
        game_list = sheet_manager.get_multiple_str_cells(f"'{self.GAME_LIST_SHEET}'!{self.GAME_LIST_CELLS}")
        return game_list
