from dataclasses import dataclass, field
from typing import Optional

import gspread
from pydantic import BaseModel, ConfigDict

from model.crawl_model import OfferItem, StockNumInfo
from model.enums import StockType
from utils.sheet_operator import query_multi_model_from_worksheet
from .sheet_model import Product, StockInfo, G2G, FUN, BIJ, ExtraInfor


@dataclass
class Product_:
    CHECK: Optional[str] = field(default=None)
    Product_name: Optional[str] = field(default=None)
    Note: Optional[str] = field(default=None)
    Last_Update: Optional[str] = field(default=None)
    Product_link: Optional[str] = field(default=None)
    PRODUCT_COMPARE: Optional[str] = field(default=None)
    DONGIAGIAM_MIN: Optional[float] = field(default=None)
    DONGIAGIAM_MAX: Optional[float] = field(default=None)
    DONGIA_LAMTRON: Optional[float] = field(default=None)
    EXCLUDE_ADS: Optional[str] = field(default=None)
    DELIVERY_TIME: Optional[str] = field(default=None)
    FEEDBACK: Optional[str] = field(default=None)
    MIN_UNIT: Optional[int] = field(default=None)
    MINSTOCK: Optional[int] = field(default=None)
    IDSHEET_MIN: Optional[str] = field(default=None)
    SHEET_MIN: Optional[str] = field(default=None)
    CELL_MIN: Optional[str] = field(default=None)
    IDSHEET_MIN2: Optional[str] = field(default=None)
    SHEET_MIN2: Optional[str] = field(default=None)
    CELL_MIN2: Optional[str] = field(default=None)
    DELIVERY0: Optional[str] = field(default=None)
    DELIVERY1: Optional[str] = field(default=None)
    STOCKREAD: Optional[str] = field(default=None)
    IDSHEET_MAX: Optional[str] = field(default=None)
    SHEET_MAX: Optional[str] = field(default=None)
    CELL_MAX: Optional[str] = field(default=None)
    IDSHEET_STOCK: Optional[str] = field(default=None)
    SHEET_STOCK: Optional[str] = field(default=None)
    CELL_STOCK: Optional[str] = field(default=None)
    IDSHEET_STOCK2: Optional[str] = field(default=None)
    SHEET_STOCK2: Optional[str] = field(default=None)
    CELL_STOCK2: Optional[str] = field(default=None)
    STOCK_LIMIT: Optional[int] = field(default=None)
    STOCK_LIMIT2: Optional[int] = field(default=None)
    STOCK_MAX: Optional[int] = field(default=None)
    STOCK_FAKE: Optional[int] = field(default=None)
    G2G_CHECK: Optional[str] = field(default=None)
    G2G_PROFIT: Optional[float] = field(default=None)
    G2G_PRODUCT_COMPARE: Optional[str] = field(default=None)
    G2G_DELIVERY_TIME: Optional[str] = field(default=None)
    G2G_STOCK: Optional[int] = field(default=None)
    G2G_MINUNIT: Optional[int] = field(default=None)
    G2G_QUYDOIDONVI: Optional[float] = field(default=None)
    EXCEPTION1: Optional[str] = field(default=None)
    SELLERNAME1: Optional[str] = field(default=None)
    G2G_IDSHEET_BLACKLIST: Optional[str] = field(default=None)
    G2G_SHEET_BLACKLIST: Optional[str] = field(default=None)
    G2G_CELL_BLACKLIST: Optional[str] = field(default=None)
    FUN_CHECK: Optional[str] = field(default=None)
    FUN_PROFIT: Optional[float] = field(default=None)
    FUN_DISCOUNTFEE: Optional[float] = field(default=None)
    FUN_PRODUCT_COMPARE: Optional[str] = field(default=None)
    NAME2: Optional[str] = field(default=None)
    FUN_FILTER21: Optional[str] = field(default=None)
    FUN_FILTER22: Optional[str] = field(default=None)
    FUN_FILTER23: Optional[str] = field(default=None)
    FUN_FILTER24: Optional[str] = field(default=None)
    PRICE2: Optional[float] = field(default=None)
    FACTION2: Optional[str] = field(default=None)
    FUN_STOCK: Optional[int] = field(default=None)
    FUN_IDSHEET_BLACKLIST: Optional[str] = field(default=None)
    FUN_SHEET_BLACKLIST: Optional[str] = field(default=None)
    FUN_CELL_BLACKLIST: Optional[str] = field(default=None)
    BIJ_CHECK: Optional[str] = field(default=None)
    BIJ_PROFIT: Optional[float] = field(default=None)
    BIJ_NAME: Optional[str] = field(default=None)
    BIJ_SERVER: Optional[str] = field(default=None)
    BIJ_DELIVERY_METHOD: Optional[str] = field(default=None)
    BIJ_STOCKMIN: Optional[int] = field(default=None)
    BIJ_STOCKMAX: Optional[int] = field(default=None)
    HESONHANDONGIA3: Optional[float] = field(default=None)


class Row:
    row_index: int
    product: Product
    stock_info: StockInfo
    g2g: G2G
    fun: FUN
    bij: BIJ
    extra: ExtraInfor

    def __init__(
            self,
            row_index: int,
            worksheet: gspread.worksheet.Worksheet,
            product: Product,
            stock_info: StockInfo,
            g2g: G2G,
            fun: FUN,
            bij: BIJ,
            extra: ExtraInfor,
    ) -> None:
        self.row_index = row_index
        self.worksheet = worksheet
        self.product = product
        self.stock_info = stock_info
        self.g2g = g2g
        self.fun = fun
        self.bij = bij
        self.extra = extra

    @staticmethod
    def from_row_index(
            worksheet,
            row_index: int,
    ) -> "Row":
        try:
            return Row(
                row_index,
                worksheet,
                *query_multi_model_from_worksheet(
                    worksheet, [Product, StockInfo, G2G, FUN, BIJ, ExtraInfor], row_index
                ),  # type: ignore
            )
        except Exception as e:
            raise Exception(f"Error getting row: {e}")


class PriceInfo(BaseModel):
    price_min: float
    price_mac: float
    adjusted_price: float
    range_adjust: float | None = None
    offer_item: OfferItem
    stock_type: StockType
    stock_num_info: StockNumInfo
    ref_seller: str | None

