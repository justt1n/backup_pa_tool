import copy
import random
from typing import Any

import gspread

from decorator.retry import retry
from decorator.time_execution import time_execution
from model.crawl_model import G2GOfferItem, OfferItem, DeliveryTime, StockNumInfo
from model.enums import StockType
from model.payload import PriceInfo, Row
from model.sheet_model import G2G, Product, StockInfo
from utils.common_utils import getCNYRate
from utils.g2g_extract import g2g_extract_offer_items
from utils.ggsheet import (
    GSheet,
)
from utils.selenium_util import SeleniumUtil


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
    if offer_item.seller.name in black_list:
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
    if stock_1 != -1 and stock_1 >= stock_info.STOCK_LIMIT:
        stock_type = StockType.stock_1
    if stock_2 != -1 and stock_2 >= stock_info.STOCK_LIMIT2:
        stock_type = StockType.stock_2
    return stock_type, stock_num_info


@retry(retries=3, delay=0.25)
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
            g2g_min_price = (row.g2g.get_g2g_price()
                             * row.g2g.G2G_PROFIT
                             * row.g2g.G2G_QUYDOIDONVI, "Get directly from sheet")
            print(f"\nG2G min price: {g2g_min_price}")
        except Exception as e:
            raise Exception(f"Error getting G2G price: {e}")

    fun_min_price = None
    if row.fun.FUN_CHECK == 1:
        try:
            fun_min_price = (row.fun.get_fun_price()
                             * row.fun.FUN_PROFIT
                             * row.fun.FUN_DISCOUNTFEE
                             * row.fun.FUN_QUYDOIDONVI, "Get directly from sheet")
        except Exception as e:
            raise Exception(f"Error getting FUN price: {e}")

    bij_min_price = None
    CNY_RATE = getCNYRate()
    if row.bij.BIJ_CHECK == 1:
        try:
            bij_min_price = (row.bij.get_bij_price()
                             * row.bij.BIJ_PROFIT
                             * row.bij.BIJ_QUYDOIDONVI
                             * CNY_RATE, "Get directly from sheet")
        except Exception as e:
            raise Exception(f"Error getting BIJ price: {e}")

    return min(
        [i for i in [g2g_min_price, fun_min_price, bij_min_price] if i is not None and i[0] > 0],
        key=lambda x: x[0]
    ), [g2g_min_price, fun_min_price, bij_min_price]


@time_execution
@retry(retries=3, delay=0.25, exception=Exception)
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
    offer_items_copy = copy.deepcopy(offer_items)

    # Ensure min_offer_item is valid before proceeding
    valid_filtered_offer_items = filter_valid_offer_items(
        row.product,
        offer_items_copy,  # Use the copy for filtering
        black_list=black_list
    )
    if not valid_filtered_offer_items:
        # print("No valid offer items after initial filtering for min_offer_item.")
        return None  # Cannot proceed without a base offer item

    min_offer_item = OfferItem.min_offer_item(valid_filtered_offer_items)

    if min_offer_item is None or min_offer_item.quantity == 0:  # Check for None and zero quantity
        # print("Min offer item is None or has zero quantity.")
        return None

    _ref_seller = min_offer_item.seller.name
    min_offer_item.price = min_offer_item.price / min_offer_item.quantity  # Price per unit
    _ref_price = min_offer_item.price
    stock_fake_items = None

    product_min_price: float = -1.0
    product_max_price: float = -1.0
    adjusted_price: float = 0.0
    range_adjust: float = 0.0

    if stock_type is StockType.stock_1:
        product_min_price = float(row.product.min_price_stock_1(gsheet))
        product_max_price = float(row.product.max_price_stock_1(gsheet))

    elif stock_type is StockType.stock_2:
        product_min_price = float(row.product.min_price_stock_2(gsheet))
        product_max_price = float(row.product.max_price_stock_2(gsheet))

    elif stock_type is StockType.stock_fake:
        stock_fake_price_tuple, stock_fake_items = calculate_price_stock_fake(
            gsheet=gsheet, row=row, quantity=min_offer_item.quantity, hostdata=BIJ_HOST_DATA, selenium=selenium
        )
        if stock_fake_price_tuple is None or stock_fake_price_tuple[0] <= 0:  # Ensure valid price
            # print("Stock fake price is None or not positive.")
            return None

        stock_fake_price_value = stock_fake_price_tuple[0]

        # These are the min/max for the "stock_fake" scenario itself
        product_min_price = float(row.product.get_stock_fake_min_price())  # Renamed for clarity within block
        product_max_price = float(row.product.get_stock_fake_max_price())  # Renamed for clarity

        range_adjust = random.uniform(row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX)

        if int(product_min_price) == -1 and int(product_max_price) == -1:
            # Filter items not in blacklist for finding closest if no min/max defined
            valid_offers_for_closest = [item for item in offer_items_copy if
                                        item.seller.name not in black_list and item.quantity > 0]
            if not valid_offers_for_closest:
                # print("No valid offers to find closest when stock_fake min/max are -1.")
                return None  # Cannot determine price

            # Find offer item closest to stock_fake_price_value (competitor price)
            closest_offer_to_competitor = min(
                valid_offers_for_closest,
                key=lambda item: abs((item.price / item.quantity) - stock_fake_price_value)
            )
            adjusted_price = round(
                (closest_offer_to_competitor.price / closest_offer_to_competitor.quantity) - range_adjust,
                row.product.DONGIA_LAMTRON,
            )
            # Ensure our price is at least the competitor's price (or our calculated version of it)
            adjusted_price = max(adjusted_price, stock_fake_price_value)

        elif product_min_price != -1.0 and stock_fake_price_value < product_min_price:
            adjusted_price = product_min_price
        elif product_max_price != -1.0 and stock_fake_price_value > product_max_price:
            adjusted_price = product_max_price
        else:
            # Price based on competitor + random adjustment (if competitor price is within our min/max or no min/max)
            adjusted_price = round(
                stock_fake_price_value + range_adjust,  # User may want to be above competitor
                row.product.DONGIA_LAMTRON,
            )

        # General clamping based on our own product's min_offer_item and defined fake_stock min/max
        # Ensure adjusted_price is not below our own min_offer_item's price (minus an adjustment)
        # And not below the product_min_price for stock_fake
        lower_bound_candidate = min_offer_item.price - range_adjust  # Potential price based on our cheapest valid offer

        current_lower_bound = lower_bound_candidate
        if product_min_price != -1.0:
            current_lower_bound = max(lower_bound_candidate, product_min_price)

        adjusted_price = max(adjusted_price, current_lower_bound)

        if product_max_price != -1.0:
            adjusted_price = min(adjusted_price, product_max_price)

        adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

        # Attempt to undercut a slightly higher priced seller
        # Sort by price per unit
        sorted_valid_offers = sorted([item for item in offer_items_copy if item.quantity > 0],
                                     key=lambda item: item.price / item.quantity)

        _profit_margin_for_undercut = random.uniform(row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX)
        closest_price, closest_seller = get_closest_offer_item(sorted_valid_offers, adjusted_price,
                                                               _profit_margin_for_undercut, black_list)

        if closest_price != -1 and closest_price > 0:  # Ensure positive price
            adjusted_price = closest_price
            _ref_seller = closest_seller
            _ref_price = closest_price + _profit_margin_for_undercut  # This is the target competitor price we undercut

            # Re-clamp and re-round after getting closest_price
            if product_min_price != -1.0:
                adjusted_price = max(adjusted_price, product_min_price)
            if product_max_price != -1.0:
                adjusted_price = min(adjusted_price, product_max_price)
            adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

        _display_min_price = round(product_min_price, 4) if product_min_price != -1.0 else -1.0
        _display_max_price = round(product_max_price, 4) if product_max_price != -1.0 else -1.0

        return PriceInfo(
            price_min=_display_min_price,
            price_mac=_display_max_price,
            adjusted_price=adjusted_price,
            offer_item=min_offer_item,  # This is the original min_offer_item (price per unit)
            stock_type=stock_type,
            stock_num_info=stock_num_info,
            ref_seller=_ref_seller,
            ref_price=_ref_price
        ), stock_fake_items

    # For stock_1 and stock_2 types
    range_adjust = random.uniform(
        row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX
    )

    # Initial adjusted price based on min_offer_item and product's own min/max for this stock type
    if product_min_price != -1.0 and min_offer_item.price < product_min_price:
        adjusted_price = product_min_price
    elif product_max_price != -1.0 and min_offer_item.price > product_max_price:
        adjusted_price = product_max_price
    else:  # min_offer_item.price is within bounds, or bounds are not set
        adjusted_price = round(
            min_offer_item.price - range_adjust,  # Undercut our own cheapest offer slightly
            row.product.DONGIA_LAMTRON,
        )

    # Re-apply clamping with product's min/max for this stock type
    # Ensure adjusted_price is not below (our min_offer_item - range_adjust)
    # And also not below the defined product_min_price for this stock type

    lower_bound_candidate_stock12 = min_offer_item.price - range_adjust
    current_lower_bound_stock12 = lower_bound_candidate_stock12
    if product_min_price != -1.0:
        current_lower_bound_stock12 = max(lower_bound_candidate_stock12, product_min_price)

    adjusted_price = max(adjusted_price, current_lower_bound_stock12)

    if product_max_price != -1.0:
        adjusted_price = min(adjusted_price, product_max_price)

    adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

    # Attempt to undercut a slightly higher priced seller from the general offers list
    # Sort by price per unit
    sorted_valid_offers_stock12 = sorted([item for item in offer_items_copy if item.quantity > 0],
                                         key=lambda item: item.price / item.quantity)
    _profit_margin_for_undercut_stock12 = random.uniform(row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX)
    closest_price, closest_seller = get_closest_offer_item(sorted_valid_offers_stock12, adjusted_price,
                                                           _profit_margin_for_undercut_stock12, black_list)

    if closest_price != -1 and closest_price > 0:  # Ensure positive price
        adjusted_price = closest_price
        _ref_seller = closest_seller
        _ref_price = closest_price + _profit_margin_for_undercut_stock12  # Target competitor price

        # Re-clamp and re-round after getting closest_price
        if product_min_price != -1.0:
            adjusted_price = max(adjusted_price, product_min_price)
        if product_max_price != -1.0:
            adjusted_price = min(adjusted_price, product_max_price)
        adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

    _display_product_min_price = product_min_price if product_min_price != -1.0 else -1.0
    _display_product_max_price = product_max_price if product_max_price != -1.0 else -1.0

    return PriceInfo(
        price_min=_display_product_min_price,
        price_mac=_display_product_max_price,
        adjusted_price=adjusted_price,
        offer_item=min_offer_item,  # This is the original min_offer_item (price per unit)
        stock_type=stock_type,
        range_adjust=range_adjust,  # This might be the initial range_adjust
        stock_num_info=stock_num_info,
        ref_seller=_ref_seller,
        ref_price=_ref_price
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


def get_closest_offer_item(
        sorted_offer_items: list[OfferItem],
        price: float,
        profit: float,
        black_list: list[str]
):
    if len(sorted_offer_items) >= 1:
        if price < sorted_offer_items[0].price:
            return -1, "Keep"
    # Filter offer items that have a price above the target price
    above_price_items = [item for item in sorted_offer_items if (item.price / item.quantity) > price and item.seller.name not in black_list]

    if not above_price_items:
        # If no items are above the target price, return the item with the highest price
        closest_item = max(sorted_offer_items, key=lambda item: item.price / item.quantity)
    else:
        # Find the item with the lowest price among those above the target price
        closest_item = min(above_price_items, key=lambda item: item.price / item.quantity)

    # Create a copy of the closest item
    adjusted_item = copy.deepcopy(closest_item)

    # Adjust the price by the profit factor
    adjusted_item.price = (adjusted_item.price / adjusted_item.quantity) - profit

    return adjusted_item.price , adjusted_item.seller.name
