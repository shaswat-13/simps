from django.db import connection, transaction
from decimal import Decimal
from datetime import datetime

def get_current_savings(user_id):
    now = datetime.now()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT savings_amount
            FROM Savings
            WHERE user_id = %s
            ORDER BY year DESC, month DESC
            LIMIT 1
        """, [user_id])

        result = cursor.fetchone()

    return Decimal(result[0]) if result else Decimal("0")

# get another equity from the global equity table
def get_next_equity(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ge.equity_id, ge.symbol, ge.equity_name, ge.current_price, ge.sector
            FROM Global_Equities ge
            LEFT JOIN Personal_Portfolio pp 
                ON ge.equity_id = pp.equity_id 
                AND pp.user_id = %s
            WHERE pp.equity_id IS NULL
            ORDER BY RANDOM()
            LIMIT 1
        """, [user_id])

        return cursor.fetchone()

# when user decides to purchase a stock, add it to their personal portfolio 
# and log into expenses and recalculate savings
# make this atomic transaction -> either executes or rolls back 
@transaction.atomic
def process_purchase(user_id, equity_id, amount):
    now = datetime.now()
    amount = Decimal(amount)

    with connection.cursor() as cursor:
        # 1. Fetch current savings and lock row
        cursor.execute("""
            SELECT savings_id, savings_amount
            FROM Savings
            WHERE user_id = %s
            ORDER BY year DESC, month DESC
            LIMIT 1
            FOR UPDATE
        """, [user_id])
        savings_row = cursor.fetchone()

        if not savings_row:
            return {"error": "No savings record"}

        savings_id, current_savings = savings_row[0], Decimal(savings_row[1])

        if amount < 1 or amount > current_savings:
            return {"error": "Invalid amount"}

        # 2. Fetch equity price AND name
        cursor.execute("""
            SELECT current_price, equity_name
            FROM Global_Equities
            WHERE equity_id = %s
        """, [equity_id])
        
        equity_row = cursor.fetchone()
        if not equity_row:
            return {"error": "Equity not found"}

        price = Decimal(equity_row[0])
        equity_name = equity_row[1]  # Store the equity name 
        quantity = amount / price

        # 3. Handle Personal Portfolio (Update or Insert)
        cursor.execute("""
            INSERT INTO Personal_Portfolio 
                (user_id, equity_id, quantity, purchase_price, date_added)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, equity_id)
            DO UPDATE SET 
                quantity = Personal_Portfolio.quantity + EXCLUDED.quantity
        """, [user_id, equity_id, quantity, price, now.date()])
        # 4. Insert expense with the dynamic name
        # We use Python string formatting for the category text
        category_text = f"Equity Purchase: {equity_name}"
        
        cursor.execute("""
            INSERT INTO Expenses
            (user_id, month, year, amount, category)
            VALUES (%s, %s, %s, %s, %s)
        """, [
            user_id,
            now.month,
            now.year,
            amount,
            category_text  # Dynamic category name
        ])

        # 5. Update savings
        cursor.execute("""
            UPDATE Savings
            SET total_expenses = total_expenses + %s,
                savings_amount = savings_amount - %s
            WHERE savings_id = %s
        """, [amount, amount, savings_id])

    return {"success": True}