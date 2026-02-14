# Library Desk Agent

AI-powered library management with natural language. Built with Groq (free API), LangChain, and SQLite.

## Quick Start

```bash
# 1. Get free API key: https://console.groq.com/keys

# 2. Setup
copy .env.example .env
# Edit .env and add your key: GROQ_API_KEY=gsk_...

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

## What It Does

Talk naturally to manage your library:
- Search books by title or author
- Create orders and auto-reduce stock
- Restock inventory
- Update prices
- Check order status
- View inventory with low-stock alerts

## Example Scenarios

### Scenario 1: Create Order
```
You: We sold 3 copies of Clean Code to customer 2 today

Agent: Order #5 created!
       Customer: Bob Smith
       Total: $119.97
       Updated stock: Clean Code - 47 remaining
```

### Scenario 2: Restock + Search
```
You: Restock The Pragmatic Programmer by 10 and show books by Andrew Hunt

Agent: Restocked: The Pragmatic Programmer
       Previous: 30, Added: +10, New: 40
       
       Found 1 book by Andrew Hunt:
       - The Pragmatic Programmer ($44.99, 40 units)
```

### Scenario 3: Check Order
```
You: What's the status of order 3?

Agent: Order #3 - COMPLETED
       Customer: Charlie Brown
       Total: $119.85
       Items: 3x Python Crash Course @ $39.95
```

### Scenario 4: Update Price
```
You: Change price of Effective Java to 45

Agent: Price updated: Effective Java
       Old: $49.99
       New: $45.00
```

### Scenario 5: Inventory Check
```
You: Show inventory summary

Agent: Total Titles: 10
       Total Books: 318
       Total Value: $14,447.82
       
       LOW STOCK:
       - Domain-Driven Design (4 units)
```

## Features

- Natural language interface with Chainlit UI
- Accepts book titles OR ISBNs
- Multi-step operations
- Session management
- Complete chat history
- Auto stock management
- Low stock alerts (<5 units)

## Project Structure

```
library-desk-agent/
├── main.py              # Main application
├── server/
│   ├── agent_groq.py   # AI agent
│   ├── database.py     # SQLite operations
│   └── tools.py        # 6 tools
├── db/
│   ├── Schema.sql      # Database structure
│   └── Seed.sql        # Sample data
├── prompts/
│   └── System_prompt.md # Agent instructions
└── .env                # Your API key (not in repo)
```

## Seed Data

**10 Books** - Clean Code, Python Crash Course, Effective Java, etc.  
**6 Customers** - Alice, Bob, Charlie, Diana, Ethan, Fiona  
**4 Sample Orders** - Pre-populated for testing

## Tech Stack

- Python 3.8+
- Groq (Llama 3.3 70B) - Free API
- LangChain
- SQLite

## Troubleshooting

**"GROQ_API_KEY not found"**  
Create `.env` file from `.env.example` and add your key

**"Database locked"**  
Run only one instance at a time

**"Book not found"**  
Tools accept titles: `"Python"` finds `"Python Crash Course"`



**Built for librarians. Talk to your library naturally.**
