from typing import List, Dict, Any
from pydantic import BaseModel, Field
from database import db



class FindBooksInput(BaseModel):
    q: str = Field(description="Search query string")
    by: str = Field(default="title", description="Search by 'title' or 'author'")


class CreateOrderInput(BaseModel):
    customer_id: int = Field(description="Customer ID")
    items: List[Dict[str, Any]] = Field(description="List of items with 'isbn' and 'qty' keys")


class RestockBookInput(BaseModel):
    isbn: str = Field(description="ISBN or book title to search for")
    qty: int = Field(description="Quantity to add to stock")


class UpdatePriceInput(BaseModel):
    isbn: str = Field(description="ISBN or book title to search for")
    price: float = Field(description="New price")


class OrderStatusInput(BaseModel):
    order_id: int = Field(description="Order ID to check")


def find_books(q: str, by: str = "title") -> str:
    try:
        books = db.find_books(q, by)
        
        if not books:
            return f"No books found matching '{q}' in {by}."
        
        result = f"Found {len(books)} book(s):\n\n"
        for book in books:
            result += f" {book['title']}\n"
            result += f"   Author: {book['author']}\n"
            result += f"   ISBN: {book['isbn']}\n"
            result += f"   Price: ${book['price']:.2f}\n"
            result += f"   Stock: {book['stock']} units\n\n"
        
        return result.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def create_order(customer_id: int, items: List[Dict[str, Any]]) -> str:
    try:
        customer = db.get_customer(customer_id)
        if not customer:
            return f"Error: Customer ID {customer_id} not found."
        
        processed_items = []
        for item in items:
            isbn = item.get('isbn', '')
            qty = item.get('qty', 1)
            
            if not isbn.startswith('978'):
                books = db.find_books(isbn, "title")
                if not books:
                    return f"Error: No book found matching '{isbn}'."
                if len(books) > 1:
                    result = f"Multiple books found for '{isbn}'. Please specify:\n\n"
                    for b in books:
                        result += f"  • {b['title']} (ISBN: {b['isbn']})\n"
                    return result.strip()
                isbn = books[0]['isbn']
            
            processed_items.append({'isbn': isbn, 'qty': qty})
        
        result = db.create_order(customer_id, processed_items)
        
        output = f" Order #{result['order_id']} created!\n\n"
        output += f"Customer: {customer['name']} ({customer['email']})\n"
        output += f"Total: ${result['total_amount']:.2f}\n\n"
        output += "Items:\n"
        
        for item in result['items']:
            output += f"  • {item['title']} - Qty: {item['quantity']} @ ${item['price']:.2f}\n"
        
        output += "\nUpdated stock:\n"
        for book in result['updated_stock']:
            output += f"  • {book['title']}: {book['stock']} remaining\n"
        
        return output.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def restock_book(isbn: str, qty: int) -> str:
    """Restock a book"""
    try:
        book = db.get_book(isbn)
        if not book:
            if not isbn.startswith('978'):
                books = db.find_books(isbn, "title")
                if books:
                    if len(books) == 1:
                        book = books[0]
                        isbn = book['isbn']
                    else:
                        # Multiple matches - show options
                        result = f"Found {len(books)} books matching '{isbn}'. Please specify:\n\n"
                        for b in books:
                            result += f"  • {b['title']} (ISBN: {b['isbn']}) - Stock: {b['stock']}\n"
                        return result.strip()
                else:
                    return f"Error: No book found matching '{isbn}'."
            else:
                return f"Error: Book with ISBN {isbn} not found."
        
        old_stock = book['stock']
        db.update_stock(isbn, qty)
        book = db.get_book(isbn)
        
        output = f" Restocked: {book['title']}\n"
        output += f"   Previous: {old_stock}\n"
        output += f"   Added: +{qty}\n"
        output += f"   New Stock: {book['stock']}"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


def update_price(isbn: str, price: float) -> str:
    try:
        # First try direct ISBN lookup
        book = db.get_book(isbn)
        
        if not book:
            if not isbn.startswith('978'):
                books = db.find_books(isbn, "title")
                if books:
                    if len(books) == 1:
                        book = books[0]
                        isbn = book['isbn']
                    else:
                        # Multiple matches - show options
                        result = f"Found {len(books)} books matching '{isbn}'. Please specify:\n\n"
                        for b in books:
                            result += f"  • {b['title']} (ISBN: {b['isbn']}) - ${b['price']:.2f}\n"
                        return result.strip()
                else:
                    return f"Error: No book found matching '{isbn}'."
            else:
                return f"Error: Book with ISBN {isbn} not found."
        
        old_price = book['price']
        db.update_price(isbn, price)
        
        output = f" Price updated: {book['title']}\n"
        output += f"   Old: ${old_price:.2f}\n"
        output += f"   New: ${price:.2f}"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


def order_status(order_id: int) -> str:
    try:
        order = db.get_order_status(order_id)
        
        if not order:
            return f"Error: Order #{order_id} not found."
        
        output = f" Order #{order['id']} - {order['status'].upper()}\n\n"
        output += f"Customer: {order['customer_name']}\n"
        output += f"Total: ${order['total_amount']:.2f}\n"
        output += f"Date: {order['created_at']}\n\n"
        output += "Items:\n"
        
        for item in order['items']:
            output += f"  • {item['title']} by {item['author']}\n"
            output += f"    Qty: {item['quantity']} @ ${item['price_at_purchase']:.2f}\n\n"
        
        return output.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def inventory_summary() -> str:
    try:
        summary = db.get_inventory_summary()
        
        output = " INVENTORY SUMMARY\n\n"
        output += f"Total Titles: {summary['total_titles']}\n"
        output += f"Total Books: {summary['total_books']}\n"
        output += f"Total Value: ${summary['total_value']:.2f}\n\n"
        
        if summary['low_stock']:
            output += " LOW STOCK (< 5 units):\n\n"
            for book in summary['low_stock']:
                output += f"  • {book['title']}\n"
                output += f"    Stock: {book['stock']} units\n"
                output += f"    ISBN: {book['isbn']}\n\n"
        else:
            output += " All books adequately stocked.\n"
        
        return output.strip()
    except Exception as e:
        return f"Error: {str(e)}"


TOOLS = {
    'find_books': {
        'function': find_books,
        'description': 'Search for books by title or author',
        'parameters': FindBooksInput
    },
    'create_order': {
        'function': create_order,
        'description': 'Create order and reduce stock',
        'parameters': CreateOrderInput
    },
    'restock_book': {
        'function': restock_book,
        'description': 'Add quantity to book stock',
        'parameters': RestockBookInput
    },
    'update_price': {
        'function': update_price,
        'description': 'Update book price',
        'parameters': UpdatePriceInput
    },
    'order_status': {
        'function': order_status,
        'description': 'Get order details',
        'parameters': OrderStatusInput
    },
    'inventory_summary': {
        'function': inventory_summary,
        'description': 'Get inventory summary with low stock alerts',
        'parameters': None
    }
}