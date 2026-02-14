"""
Database module for Library Agent
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


DB_PATH = Path(__file__).parent.parent / "db" / "library.db"


class Database:
    """Database handler"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
        seed_path = Path(__file__).parent.parent / "db" / "seed.sql"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if schema_path.exists():
                with open(schema_path) as f:
                    cursor.executescript(f.read())
            
            cursor.execute("SELECT COUNT(*) as count FROM books")
            if cursor.fetchone()['count'] == 0:
                if seed_path.exists():
                    with open(seed_path) as f:
                        cursor.executescript(f.read())
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def find_books(self, query: str, by: str = "title") -> List[Dict]:
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if by == "author":
                cursor.execute(
                    "SELECT * FROM books WHERE author LIKE ? ORDER BY title",
                    (f"%{query}%",)
                )
            else:
                cursor.execute(
                    "SELECT * FROM books WHERE title LIKE ? ORDER BY title",
                    (f"%{query}%",)
                )
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_book(self, isbn: str) -> Optional[Dict]:
        """Get book by ISBN"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM books WHERE isbn = ?", (isbn,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def update_stock(self, isbn: str, quantity: int) -> bool:
        """Update stock"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE books SET stock = stock + ? WHERE isbn = ?",
                (quantity, isbn)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_price(self, isbn: str, price: float) -> bool:
        """Update price"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE books SET price = ? WHERE isbn = ?",
                (price, isbn)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_inventory_summary(self) -> Dict:
        """Get inventory summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_titles,
                    SUM(stock) as total_books,
                    SUM(stock * price) as total_value
                FROM books
            """)
            summary = dict(cursor.fetchone())
            
            cursor.execute("""
                SELECT isbn, title, author, stock, price
                FROM books
                WHERE stock < 5
                ORDER BY stock ASC
            """)
            summary['low_stock'] = [dict(row) for row in cursor.fetchall()]
            
            return summary
        finally:
            conn.close()
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """Get customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def create_order(self, customer_id: int, items: List[Dict[str, Any]]) -> Dict:
        """Create order and reduce stock"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
            if not cursor.fetchone():
                raise ValueError(f"Customer {customer_id} not found")
            
            total_amount = 0
            order_items = []
            
            for item in items:
                isbn = item['isbn']
                qty = item['qty']
                
                cursor.execute("SELECT * FROM books WHERE isbn = ?", (isbn,))
                book = cursor.fetchone()
                
                if not book:
                    raise ValueError(f"Book {isbn} not found")
                
                book = dict(book)
                
                if book['stock'] < qty:
                    raise ValueError(
                        f"Insufficient stock for {book['title']}. "
                        f"Available: {book['stock']}, Requested: {qty}"
                    )
                
                item_total = book['price'] * qty
                total_amount += item_total
                
                order_items.append({
                    'isbn': isbn,
                    'quantity': qty,
                    'price': book['price'],
                    'title': book['title']
                })
            
            cursor.execute(
                "INSERT INTO orders (customer_id, total_amount, status) VALUES (?, ?, ?)",
                (customer_id, total_amount, 'completed')
            )
            order_id = cursor.lastrowid
            
            for item in order_items:
                cursor.execute(
                    """INSERT INTO order_items (order_id, isbn, quantity, price_at_purchase)
                       VALUES (?, ?, ?, ?)""",
                    (order_id, item['isbn'], item['quantity'], item['price'])
                )
                
                cursor.execute(
                    "UPDATE books SET stock = stock - ? WHERE isbn = ?",
                    (item['quantity'], item['isbn'])
                )
            
            conn.commit()
            
            updated_books = []
            for item in order_items:
                cursor.execute("SELECT isbn, title, stock FROM books WHERE isbn = ?", (item['isbn'],))
                updated_books.append(dict(cursor.fetchone()))
            
            return {
                'order_id': order_id,
                'total_amount': total_amount,
                'items': order_items,
                'updated_stock': updated_books
            }
        
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_order_status(self, order_id: int) -> Optional[Dict]:
        """Get order details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT o.*, c.name as customer_name, c.email as customer_email
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = ?
            """, (order_id,))
            
            order = cursor.fetchone()
            if not order:
                return None
            
            order = dict(order)
            
            cursor.execute("""
                SELECT oi.*, b.title, b.author
                FROM order_items oi
                JOIN books b ON oi.isbn = b.isbn
                WHERE oi.order_id = ?
            """, (order_id,))
            
            order['items'] = [dict(row) for row in cursor.fetchall()]
            
            return order
        finally:
            conn.close()
    
    def log_message(self, session_id: str, role: str, content: str):
        """Log chat message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Ensure content is a string
            if not isinstance(content, str):
                content = str(content)
            
            cursor.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
        finally:
            conn.close()
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get chat history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_all_sessions(self) -> List[str]:
        """Get all session IDs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT DISTINCT session_id FROM messages ORDER BY session_id"
            )
            return [row['session_id'] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def log_tool_call(self, session_id: str, tool_name: str, args: Dict, result: Any):
        """Log tool call"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO tool_calls (session_id, tool_name, args_json, result_json)
                   VALUES (?, ?, ?, ?)""",
                (session_id, tool_name, json.dumps(args), json.dumps(result, default=str))
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
        finally:
            conn.close()


db = Database()