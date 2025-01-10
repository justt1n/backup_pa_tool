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
    _stock1: int | None = 0
    _stock2: int | None = 0

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
    G2G_CHECK: Annotated[int, "AP"]
    G2G_PROFIT: Annotated[float, "AQ"]
    G2G_PRODUCT_COMPARE: Annotated[str, "AR"]
    G2G_IDSHEET_PRICESS: Annotated[str, "AS"]
    G2G_SHEET_PRICESS: Annotated[str, "AT"]
    G2G_CELL_PRICESS: Annotated[str, "AU"]
    G2G_QUYDOIDONVI: Annotated[float, "AV"]

    def get_g2g_price(
            self
    ) -> float:
        sheet_manager = StockManager(self.G2G_IDSHEET_PRICESS)
        blacklist = sheet_manager.get_stock(f"'{self.G2G_SHEET_PRICESS}'!{self.G2G_CELL_PRICESS}")
        return blacklist


class FUN(BaseGSheetModel):
    FUN_CHECK: Annotated[int, "AW"]
    FUN_PROFIT: Annotated[float, "AX"]
    FUN_DISCOUNTFEE: Annotated[float, "AY"]
    FUN_PRODUCT_COMPARE: Annotated[str, "AZ"]
    FUN_IDSHEET_PRICESS: Annotated[str, "BA"]
    FUN_SHEET_PRICESS: Annotated[str, "BB"]
    FUN_CELL_PRICESS: Annotated[str, "BC"]
    FUN_QUYDOIDONVI: Annotated[float | None, "BD"] = None


    def get_fun_price(self) -> float:
        sheet_manager = StockManager(self.FUN_IDSHEET_PRICESS)
        blacklist = sheet_manager.get_stock(f"'{self.FUN_SHEET_PRICESS}'!{self.FUN_CELL_PRICESS}")
        return blacklist


class BIJ(BaseGSheetModel):
    BIJ_CHECK: Annotated[int, "BE"]
    BIJ_PROFIT: Annotated[float, "BF"]
    # BIJ_NAME: Annotated[str, "BG"]
    # BIJ_SERVER: Annotated[str, "BH"]
    BIJ_PRODUCT_COMPARE: Annotated[str, "BG"]
    BIJ_IDSHEET_PRICESS: Annotated[str | None, "BH"] = None
    BIJ_SHEET_PRICESS: Annotated[str | None, "BI"] = None
    BIJ_CELL_PRICESS: Annotated[str | None, "BJ"] = None
    BIJ_QUYDOIDONVI: Annotated[float | None, "BK"] = None


    def get_bij_price(self) -> float:
        sheet_manager = StockManager(self.BIJ_IDSHEET_PRICESS)
        blacklist = sheet_manager.get_stock(f"'{self.BIJ_SHEET_PRICESS}'!{self.BIJ_CELL_PRICESS}")
        return float(blacklist)


class ExtraInfor(BaseGSheetModel):
    MIN_UNIT_PER_ORDER: Annotated[int, "BL"]
    VALUE_FOR_DISCOUNT: Annotated[str | None, "BM"] = ""
    DISCOUNT: Annotated[str | None, "BN"] = ""
    DELIVERY_GUARANTEE: Annotated[int, "BO"]
