from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
import psycopg
import os
from dotenv import load_dotenv


# =========================
# Pydantic models
# =========================

class Customer(BaseModel):
    name: str
    email: str
    phone: str

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    discount: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_discount(self):
        if self.discount is not None:
            total_price = self.quantity * self.unit_price

            if self.discount > total_price:
                raise ValueError("Discount cannot be greater than total price")

        return self


class OrderCreate(BaseModel):
    customer_id: int
    items: list[OrderItemCreate] = Field(min_length=1)


# =========================
# App setup
# =========================

load_dotenv()

app = FastAPI()


# =========================
# Home
# =========================

@app.get("/")
def home():
    return {"message": "AI Automation API is working!"}

@app.post("/webhook")
def receive_webhook(data: dict):

    return {
        "message": "Webhook received",
        "data": data
    }

@app.get("/customers")
def get_customers():

    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    ) as conn:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id, name, email , phone
                FROM customers
                ORDER BY id;
            """)

            rows = cursor.fetchall()

    customers = []

    for row in rows:
        customers.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3] 
        })

    return customers

@app.get("/products")
def get_products():
    
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    ) as conn:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM products;
            """)

            rows = cursor.fetchall()

    products = []

    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "price": row[2]
        })

    return products

# =========================
# Get customer's orders
# =========================
@app.get("/customers/by-phone/{phone}")
def get_customer_by_phone(phone: str):

    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    ) as conn:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id, name, email, phone
                FROM customers
                WHERE phone = %s;
            """, (phone,))

            row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "phone": row[3]
    }

@app.get("/customers/{customer_id}/orders")
def get_customer_orders(customer_id: int):

    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    ) as conn:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    orders.id AS order_id,
                    orders.order_date,
                    products.name AS product,
                    order_items.quantity,
                    order_items.unit_price,
                    order_items.discount
                FROM orders
                JOIN order_items
                    ON orders.id = order_items.order_id
                JOIN products
                    ON products.id = order_items.product_id
                WHERE orders.customer_id = %s
                ORDER BY orders.id;
            """, (customer_id,))

            rows = cursor.fetchall()

    orders = []

    for row in rows:
        orders.append({
            "order_id": row[0],
            "order_date": row[1],
            "product": row[2],
            "quantity": row[3],
            "unit_price": row[4],
            "discount": row[5]
        })

    return orders




# =========================
# Create customer
# =========================

@app.post("/customers")
def create_customer(customer: Customer):

    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    ) as conn:

        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO customers (name, email, phone)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (customer.name, customer.email, customer.phone))

            customer_id = cursor.fetchone()[0]

        conn.commit()

    return {
        "message": "Customer created",
        "id": customer_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone
    }


# =========================
# Create order
# =========================

@app.post("/orders")
def create_order(order: OrderCreate):

    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    ) as conn:

        try:

            with conn.cursor() as cursor:

                # Step 1:
                # Check if the customer exists
                cursor.execute("""
                    SELECT id
                    FROM customers
                    WHERE id = %s;
                """, (order.customer_id,))

                customer = cursor.fetchone()

                if customer is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Customer {order.customer_id} does not exist"
                    )

                # Step 2:
                # Check that every product exists
                total = 0

                for item in order.items:

                    cursor.execute("""
                        SELECT id
                        FROM products
                        WHERE id = %s;
                    """, (item.product_id,))

                    product = cursor.fetchone()

                    if product is None:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Product {item.product_id} does not exist"
                        )

                # Step 3:
                # Create one row in the orders table
                cursor.execute("""
                    INSERT INTO orders (customer_id, order_date)
                    VALUES (%s, CURRENT_DATE)
                    RETURNING id;
                """, (order.customer_id,))

                order_id = cursor.fetchone()[0]

                # Step 4:
                # Add every product to the order
                for item in order.items:

                    cursor.execute("""
                        INSERT INTO order_items
                            (order_id, product_id, quantity, unit_price, discount)
                        VALUES
                            (%s, %s, %s, %s, %s);
                    """, (
                        order_id,
                        item.product_id,
                        item.quantity,
                        item.unit_price,
                        item.discount
                    ))

                    item_total = item.quantity * item.unit_price

                    if item.discount is not None:
                        item_total -= item.discount

                    total += item_total

            # Save everything to the database
            conn.commit()

        except HTTPException:
            conn.rollback()
            raise

        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Order creation failed",
                    "details": str(e)
                }
            )

    return {
        "message": "Order created",
        "order_id": order_id,
        "items_count": len(order.items),
        "total": total
    }

@app.get("/orders")
def get_orders():
    
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    ) as conn:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    orders.id AS order_id,
                    orders.order_date,
                    customers.name AS customer,
                    products.name AS product,
                    order_items.quantity,
                    order_items.unit_price,
                    order_items.discount
                FROM orders
                JOIN customers
                    ON customers.id = orders.customer_id
                JOIN order_items
                    ON orders.id = order_items.order_id
                JOIN products
                    ON products.id = order_items.product_id
                ORDER BY orders.id;
            """)

            rows = cursor.fetchall()

    orders = []

    for row in rows:
        orders.append({
            "order_id": row[0],
            "order_date": row[1],
            "customer": row[2],
            "product": row[3],
            "quantity": row[4],
            "unit_price": row[5],
            "discount": row[6]
        })

    return orders