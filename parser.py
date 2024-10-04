"""
Ozon Product Scraper

This module provides functionality to scrape product information from Ozon.ru search results.
It uses Playwright for web scraping and asyncio for asynchronous operations.
"""

import asyncio
import json
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Playwright, Browser, BrowserContext, ElementHandle
from curl_cffi.requests import AsyncSession

# Constants
URL_BASE = "https://www.ozon.ru"
URL_API = f"{URL_BASE}/api/composer-api.bx/page/json/v2?url="

VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

SCROLL_DEPTH = 5
SCROLL_STEP = 250
SCROLL_DELAY = 500  # milliseconds

CARD_SELECTOR = '.widget-search-result-container > div > div'
CARD_LINK_SELECTOR = 'a'
CARD_NAME_SELECTOR = 'span.tsBody500Medium'
CARD_PRICE_SELECTOR = 'css=[class*="tsHeadline500Medium"]'

DEFAULT_CARD_COUNT = 15

ADULT_CONTENT_MARKER = "userAdultModal"
ADULT_CONTENT_DESCRIPTION = "Товар для лиц старше 18 лет"


class ProductInfo:
    """Represents information about a product."""

    def __init__(self, product_id: str, short_name: str, full_name: str, description: str, url: str,
                 price: Optional[str], price_with_card: Optional[str], image_url: Optional[str]):
        self.product_id = product_id
        self.short_name = short_name
        self.full_name = full_name
        self.description = description
        self.url = url
        self.price = price
        self.price_with_card = price_with_card
        self.image_url = image_url

    def __str__(self) -> str:
        return (f"ProductInfo(id={self.product_id}, name={self.short_name}, "
                f"price={self.price}, price_with_card={self.price_with_card})")


class OzonScraper:
    """A class for scraping product information from Ozon.ru."""

    def __init__(self, url: str, count_cards: int = DEFAULT_CARD_COUNT):
        self.url = url
        self.count_cards = count_cards
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self) -> 'OzonScraper':
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        await self.page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        self.session = AsyncSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        """Close all open resources."""
        if self.session:
            await self.session.close()
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _scroll_down(self) -> None:
        """Scroll down the page to load more content."""
        for _ in range(SCROLL_DEPTH):
            await self.page.evaluate(f'window.scrollBy(0, {SCROLL_STEP})')
            await self.page.wait_for_timeout(SCROLL_DELAY)

    async def _get_product_info(self, product_url: str) -> ProductInfo:
        try:
            raw_data = await self.session.get(URL_API + product_url)
            json_data: Dict[str, Any] = json.loads(raw_data.content)

            full_name = json_data["seo"]["title"]
            if json_data["layout"][0]["component"] == ADULT_CONTENT_MARKER:
                product_id = str(full_name.split()[-1])[1:-1]
                return ProductInfo(product_id, full_name, full_name, ADULT_CONTENT_DESCRIPTION,
                                   product_url, None, None, None)

            script_data = json.loads(json_data["seo"]["script"][0]["innerHTML"])
            description = script_data["description"]
            image_url = script_data["image"]
            price = f"{script_data['offers']['price']} {script_data['offers']['priceCurrency']}"
            product_id = script_data["sku"]
            return ProductInfo(product_id, full_name, full_name, description, product_url, price, None, image_url)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing product info: {str(e)}")
            return ProductInfo("unknown", "Error", "Error", "Failed to parse product info",
                               product_url, None, None, None)

    async def _get_card_info(self, card: ElementHandle) -> Optional[ProductInfo]:
        """Extract product information from a card element."""
        try:
            card_url_element = await card.query_selector(CARD_LINK_SELECTOR)
            if not card_url_element:
                return None

            card_url = await card_url_element.get_attribute('href')
            if not card_url:
                return None

            card_name_element = await card.query_selector(CARD_NAME_SELECTOR)
            if not card_name_element:
                return None

            card_name = await card_name_element.inner_text()
            product_url = URL_BASE + card_url
            price_with_card_element = await card.query_selector(CARD_PRICE_SELECTOR)
            price_with_card = await price_with_card_element.inner_text() if price_with_card_element else None

            product_info = await self._get_product_info(card_url)
            product_info.price_with_card = price_with_card
            return product_info
        except Exception as e:
            print(f"Error processing card: {str(e)}")
            return None

    async def get_searchpage_cards(self) -> List[ProductInfo]:
        """Fetch and process product cards from the search page."""
        await self.page.goto(self.url)
        await asyncio.sleep(1)
        await self.page.reload()
        await self.page.wait_for_load_state('networkidle')

        await self._scroll_down()

        cards = await self.page.query_selector_all(CARD_SELECTOR)
        cards_info = []

        for card in cards[:self.count_cards]:
            product_info = await self._get_card_info(card)
            if product_info:
                cards_info.append(product_info)

        return cards_info


async def main() -> None:
    """Main function to demonstrate the usage of OzonScraper."""
    url = "https://www.ozon.ru/search/?text=мыл&from_global=true"
    async with OzonScraper(url) as scraper:
        search_cards = await scraper.get_searchpage_cards()
        print(f"Successfully found {len(search_cards)} cards")
        for i, card in enumerate(search_cards, 1):
            print(f"{i}) Link: https://ozon.ru/product/{card.product_id}")
            print(f"Image: {card.image_url}")
            print(f"Name: {card.short_name}")
            print(f"Article: {card.product_id}")
            print(f"Price: {card.price}")
            print(f"Price with card: {card.price_with_card}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
