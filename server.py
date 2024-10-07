"""
Ozon Product Scraper API Server

This module provides a FastAPI server for the Ozon Product Scraper.
It exposes an API endpoint for searching products on Ozon.ru and
returning the scraped information.

The server uses the OzonScraper class from the parser module to
perform the actual web scraping.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from parser import OzonScraper
import config

app = FastAPI(
    title="Ozon Product Scraper API",
    description="API для поиска и скрапинга товаров на Ozon.ru",
    version="1.0.0",
)

class SearchRequest(BaseModel):
    """
    Represents a search request.

    Attributes:
        query (str): The search query string.
    """
    query: str

class ProductInfoResponse(BaseModel):
    """
    Represents the response format for product information.

    Attributes:
        product_id (str): Unique identifier for the product.
        short_name (str): Short name or title of the product.
        full_name (str): Full name or title of the product.
        description (str): Product description.
        url (str): URL of the product page.
        price (str | None): Price of the product (if available).
        price_with_card (str | None): Price with Ozon card discount (if available).
        image_url (str | None): URL of the product image (if available).
    """
    product_id: str
    short_name: str
    full_name: str
    description: str
    url: str
    price: str | None
    price_with_card: str | None
    image_url: str | None

class SearchResponse(BaseModel):
    """
    Represents the response format for a search query.

    Attributes:
        results (List[ProductInfoResponse]): List of product information results.
    """
    results: List[ProductInfoResponse]

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Perform a search on Ozon.ru and return scraped product information.

    Args:
        request (SearchRequest): The search request containing the query.

    Returns:
        SearchResponse: A list of product information results.

    Raises:
        HTTPException: If an error occurs during scraping or processing.
    """
    url = f"https://www.ozon.ru/search/?text={request.query}&from_global=true"

    try:
        async with OzonScraper(url) as scraper:
            search_cards = await scraper.get_searchpage_cards()

        results = [
            ProductInfoResponse(
                product_id=card.product_id,
                short_name=card.short_name,
                full_name=card.full_name,
                description=card.description,
                url=f"https://ozon.ru/product/{card.product_id}",
                price=card.price,
                price_with_card=card.price_with_card,
                image_url=card.image_url
            )
            for card in search_cards
        ]

        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)