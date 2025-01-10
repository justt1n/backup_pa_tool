from typing import Final
import requests
from decorator.retry import retry
from requests import HTTPError
from bs4 import BeautifulSoup, Tag

from model.crawl_model import DeliveryTime, TimeUnit, G2GOfferItem
from .exceptions import G2GCrawlerError

import re


@retry(retries=5, delay=1.2, exception=HTTPError)
def __get_soup(
        url: str,
) -> BeautifulSoup:
    res = requests.get(
        url=url,
        cookies={
            "g2g_regional": '{"country": "VN", "currency": "USD", "language": "en"}'
        },
    )
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def __g2g_extract_offer_items_from_soup(
        soup: BeautifulSoup,
) -> list[G2GOfferItem]:
    g2g_offer_items = []

    for offer_item_tag in soup.select(
            "#pre_checkout_sls_offer .other_offer-desk-main-box"
    ):
        g2g_offer_items.append(
            G2GOfferItem(
                seller_name=__g2g_extract_seller_name(offer_item_tag),
                delivery_time=__g2g_extract_delivery_time(offer_item_tag),
                stock=__g2g_extract_stock(offer_item_tag),
                min_purchase=__g2g_extract_min_purchase(offer_item_tag),
                price_per_unit=__g2g_extract_price_per_unit(offer_item_tag),
            )
        )

    return g2g_offer_items


def __g2g_extract_seller_name(
        tag: Tag,
) -> str:
    seller_name_tag = tag.select_one(".seller__name-detail")
    if seller_name_tag:
        return seller_name_tag.get_text(strip=True)
    raise G2GCrawlerError("Can't get seller name")


def __g2g_extract_delivery_time(
        tag: Tag,
) -> DeliveryTime:
    UNIT_MAP: Final[dict[str, str]] = {
        "h": "Hours",
    }

    for flex_tag in tag.select(".flex-1.align-self"):
        if "Delivery speed" in flex_tag.get_text(strip=True):
            lower_tag = flex_tag.select_one(".offer__content-lower-items")
            if lower_tag:
                pattern = r"(\d+)([a-zA-Z]*)"
                match = re.match(pattern, lower_tag.get_text(strip=True))
                if match:
                    value = match.group(1)
                    unit = match.group(2)
                    if unit in UNIT_MAP:
                        return DeliveryTime(
                            value=int(value),
                            unit=TimeUnit(UNIT_MAP[unit]),
                        )
    raise G2GCrawlerError("Can't extract delivery time")


def __g2g_extract_stock(
        tag: Tag,
) -> int:
    for flex_tag in tag.select(".flex-1.align-self"):
        if "Stock" in flex_tag.get_text(strip=True):
            lower_tag = flex_tag.select_one(".offer__content-lower-items")
            if lower_tag:
                pattern = r"(\d+)([a-zA-Z]*)"
                lower_tag_text = lower_tag.get_text(strip=True).replace(",", "")
                match = re.match(pattern, lower_tag_text)
                if match:
                    value = match.group(1)
                    return int(value)
    raise G2GCrawlerError("Can't extract Stock")


def __g2g_extract_min_purchase(
        tag: Tag,
) -> int:
    for flex_tag in tag.select(".flex-1.align-self"):
        if "Min. purchase" in flex_tag.get_text(strip=True):
            lower_tag = flex_tag.select_one(".offer__content-lower-items")
            if lower_tag:
                pattern = r"(\d+)([a-zA-Z]*)"
                lower_tag_text = lower_tag.get_text(strip=True).replace(",", "")
                match = re.match(pattern, lower_tag_text)
                if match:
                    value = match.group(1)
                    return int(value)
    raise G2GCrawlerError("Can't extract Min purchase")


def __g2g_extract_price_per_unit(
        tag: Tag,
) -> float:
    price_tag = tag.select_one(".offer-price-amount")
    if price_tag:
        return float(price_tag.get_text(strip=True))

    raise G2GCrawlerError("Can't extract Price per unit")


@retry(retries=10, delay=0.25, exception=HTTPError)
def g2g_extract_offer_items(
        url: str,
) -> list[G2GOfferItem]:
    soup = __get_soup(url)
    return __g2g_extract_offer_items_from_soup(soup)
