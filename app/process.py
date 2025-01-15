import random
from typing import Any

import gspread

from decorator.retry import retry
from decorator.time_execution import time_execution
from model.crawl_model import G2GOfferItem, OfferItem, DeliveryTime, FUNOfferItem, StockNumInfo
from model.enums import StockType
from model.payload import PriceInfo, Row
from model.sheet_model import G2G, Product, StockInfo
from utils.biji_extract import bij_lowest_price
from utils.fun_extract import fun_extract_offer_items
from utils.g2g_extract import g2g_extract_offer_items
from utils.ggsheet import (
    GSheet,
)
from utils.selenium_util import SeleniumUtil
from utils.common_utils import getCNYRate


def get_row_run_index(
        worksheet: gspread.worksheet.Worksheet,
        col_check_index: int = 2,
        value_check: Any = "1",
) -> list[int]:
    row_indexes: list[int] = []
    for i, row_value in enumerate(worksheet.col_values(col_check_index), start=1):
        if row_value == value_check:
            row_indexes.append(i)

    return row_indexes


def is_valid_offer_item(
        product: Product,
        offer_item: OfferItem,
        black_list: list[str]
) -> bool:
    product_delivery_time = DeliveryTime.from_text(product.DELIVERY_TIME)
    if (
            offer_item.delivery_time is None
            or offer_item.delivery_time > product_delivery_time
    ):
        return False
    # if not offer_item.seller.feedback_count:
    #     offer_item.seller.feedback_count = 0
    # elif offer_item.seller.feedback_count < product.FEEDBACK:
    #     print(f"Feedback count: {offer_item.seller.feedback_count} for seller {offer_item.seller.name}, ignore")
    #     return False
    if offer_item.seller in black_list:
        return False
    if offer_item.min_unit is None or offer_item.min_unit > product.MIN_UNIT:
        return False
    if offer_item.min_stock is None or offer_item.min_stock < product.MINSTOCK:
        return False

    return True


def filter_valid_offer_items(
        product: Product,
        offer_items: list[OfferItem],
        black_list: list[str],
) -> list[OfferItem]:
    return [
        offer_item
        for offer_item in offer_items
        if is_valid_offer_item(product, offer_item, black_list)
    ]


def is_change_price(
        product: Product,
        offer_items: list[OfferItem],
        black_list: list[str],
) -> bool:
    if product.CHECK == 0:
        return False

    if product.EXCLUDE_ADS == 0:  # TODO:
        return False

    filtered_offer_items = filter_valid_offer_items(product, offer_items, black_list)
    if len(filtered_offer_items) == 0:
        return False

    return True


def identify_stock(
        gsheet: GSheet,
        stock_info: StockInfo,
) -> [StockType, StockNumInfo]:
    stock_1, stock_2 = stock_info.get_stocks()

    stock_fake = stock_info.STOCK_FAKE

    stock_num_info = StockNumInfo(
        stock_1=stock_1,
        stock_2=stock_2,
        stock_fake=stock_fake,
    )

    stock_type = StockType.stock_fake
    if stock_1 >= stock_info.STOCK_LIMIT:
        stock_type = StockType.stock_1
    if stock_2 >= stock_info.STOCK_LIMIT2:
        stock_type = StockType.stock_2
    return stock_type, stock_num_info


@retry(retries=5, delay=0.25)
def calculate_price_stock_fake(
        gsheet: GSheet,
        row: Row,
        quantity: int,
        hostdata: dict,
        selenium: SeleniumUtil,
):
    g2g_min_price = None
    if row.g2g.G2G_CHECK == 1:
        try:
            g2g_min_price = (round(row.g2g.get_g2g_price()
                                   * row.g2g.G2G_PROFIT
                                   * row.g2g.G2G_QUYDOIDONVI, 4), "Get directly from sheet")
            print(f"\nG2G min price: {g2g_min_price}")
        except Exception as e:
            raise Exception(f"Error getting G2G price: {e}")

    fun_min_price = None
    if row.fun.FUN_CHECK == 1:
        try:
            fun_min_price = (round(row.fun.get_fun_price()
                                   * row.fun.FUN_PROFIT
                                   * row.fun.FUN_DISCOUNTFEE
                                   * row.fun.FUN_QUYDOIDONVI, 4), "Get directly from sheet")
        except Exception as e:
            raise Exception(f"Error getting FUN price: {e}")

    bij_min_price = None
    CNY_RATE = getCNYRate()
    if row.bij.BIJ_CHECK == 1:
        try:
            bij_min_price = (round(row.bij.get_bij_price()
                                    * row.bij.BIJ_PROFIT
                                    * row.bij.BIJ_QUYDOIDONVI
                                    * CNY_RATE, 4), "Get directly from sheet")
        except Exception as e:
            raise Exception(f"Error getting BIJ price: {e}")

    return min(
        [i for i in [g2g_min_price, fun_min_price, bij_min_price] if i is not None and i[0] > 0],
        key=lambda x: x[0]
    ), [g2g_min_price, fun_min_price, bij_min_price]


@time_execution
#TODO
@retry(retries=5, delay=0.5, exception=Exception)
def calculate_price_change(
        gsheet: GSheet,
        row: Row,
        offer_items: list[OfferItem],
        BIJ_HOST_DATA: dict,
        selenium: SeleniumUtil,
        black_list: list[str],
) -> None | tuple[PriceInfo, list[tuple[float, str] | None]] | tuple[PriceInfo, None]:
    stock_type, stock_num_info = identify_stock(
        gsheet,
        row.stock_info,
    )

    min_offer_item = OfferItem.min_offer_item(
        filter_valid_offer_items(
            row.product,
            offer_items,
            black_list=black_list
        )
    )
    min_offer_item.price = round(min_offer_item.price / min_offer_item.quantity, 4)
    stock_fake_items = None
    if stock_type is StockType.stock_1:
        product_min_price = row.product.min_price_stock_1(gsheet)
        product_max_price = row.product.max_price_stock_1(gsheet)

    elif stock_type is StockType.stock_2:
        product_min_price = row.product.min_price_stock_2(gsheet)
        product_max_price = row.product.max_price_stock_2(gsheet)

    elif stock_type is StockType.stock_fake:
        (stock_fake_price, stock_fake_items) = calculate_price_stock_fake(
            gsheet=gsheet, row=row, quantity=min_offer_item.quantity, hostdata=BIJ_HOST_DATA, selenium=selenium
        )
        if stock_fake_price is None:
            return None
        stock_fake_min_price = int(row.product.get_stock_fake_min_price())
        stock_fake_max_price = int(row.product.get_stock_fake_max_price())
        range_adjust = None
        if stock_fake_min_price == -1 and stock_fake_max_price == -1:
            adjusted_price = stock_fake_price[0]
        elif stock_fake_price[0] < stock_fake_min_price:  # type: ignore
            adjusted_price = stock_fake_min_price
        elif stock_fake_price[0] > stock_fake_max_price:  # type: ignore
            adjusted_price = stock_fake_max_price
        else:
            range_adjust = random.uniform(
                row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX
            )
            adjusted_price = round(
                stock_fake_price[0] - range_adjust,  # type: ignore
                row.product.DONGIA_LAMTRON,
            )
        return PriceInfo(
            price_min=round(stock_fake_min_price, 4),
            price_mac=round(stock_fake_max_price, 4),
            adjusted_price=round(adjusted_price, 4),
            offer_item=min_offer_item,
            stock_type=stock_type,
            stock_num_info=stock_num_info,
        ), stock_fake_items

    range_adjust = None
    if min_offer_item.price < product_min_price:  # type: ignore
        adjusted_price = product_min_price
    elif min_offer_item.price > product_max_price:  # type: ignore
        adjusted_price = product_max_price
    else:
        range_adjust = random.uniform(
            row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX
        )
        adjusted_price = round(
            min_offer_item.price - range_adjust,  # type: ignore
            row.product.DONGIA_LAMTRON,
        )
    return PriceInfo(
        price_min=product_min_price,
        price_mac=product_max_price,
        adjusted_price=round(adjusted_price, row.product.DONGIA_LAMTRON),  # type: ignore
        offer_item=min_offer_item,
        stock_type=stock_type,
        range_adjust=range_adjust,
        stock_num_info=stock_num_info,
    ), stock_fake_items


def g2g_lowest_price(
        gsheet: GSheet,
        g2g: G2G,
) -> G2GOfferItem:
    g2g_offer_items = g2g_extract_offer_items(g2g.G2G_PRODUCT_COMPARE)
    filtered_g2g_offer_items = G2GOfferItem.filter_valid_g2g_offer_item(
        g2g,
        g2g_offer_items,
        g2g.get_g2g_price(),
    )
    return G2GOfferItem.min_offer_item(filtered_g2g_offer_items)
