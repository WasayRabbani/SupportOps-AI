import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
DB_NAME = "ecommerce.db"

# We want some controlled messiness
STATUSES = ["Delivered", "In Transit", "Delayed", "Damaged", "Lost"]
CARRIERS = ["FedEx", "UPS", "USPS", "DHL"]
PAYMENT_STATUSES = ["Paid", "Refunded", "Failed", "Pending"]
LOYALTY = ["Gold", "Silver", "Bronze", None]  # Some won't have loyalty status

def get_messy_phone():
    # Intentionally messy phone numbers (missing, weird formats)
    formats = [
        fake.phone_number(),
        f"+1-{fake.numerify('###-###-####')}",
        fake.numerify('(###) ###-####'),
        "N/A",
        ""
    ]
    return random.choice(formats)

def generate_data(num_customers=100, num_orders=300):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"Generating {num_customers} customers...")
    customer_ids = []
    for _ in range(num_customers):
        c_id = f"CUST-{fake.unique.random_number(digits=5)}"
        customer_ids.append(c_id)
        name = fake.name()
        
        # Introduce some missing names for messiness
        if random.random() < 0.05:
            name = "" 
        
        email = fake.email()
        # Introduce broken emails for messiness
        if random.random() < 0.05:
            email = email.replace("@", "") 

        cursor.execute(
            "INSERT INTO customers (customer_id, name, email, loyalty_status, account_created, phone_number) VALUES (?, ?, ?, ?, ?, ?)",
            (c_id, name, email, random.choice(LOYALTY), str(fake.date_between(start_date='-2y', end_date='today')), get_messy_phone())
        )

    print(f"Generating {num_orders} orders...")
    for _ in range(num_orders):
        o_id = f"ORD-{fake.unique.random_number(digits=6)}"
        c_id = random.choice(customer_ids)
        order_date = fake.date_between(start_date='-1y', end_date='today')
        
        total_amount = round(random.uniform(15.0, 1500.0), 2)
        payment = random.choice(PAYMENT_STATUSES)

        cursor.execute(
            "INSERT INTO orders (order_id, customer_id, order_date, total_amount, payment_status, shipping_address) VALUES (?, ?, ?, ?, ?, ?)",
            (o_id, c_id, str(order_date), total_amount, payment, fake.address().replace('\n', ', '))
        )

        # Generate 1-3 items per order
        num_items = random.randint(1, 3)
        for _ in range(num_items):
            i_id = f"ITEM-{fake.unique.random_number(digits=7)}"
            price = round(total_amount / num_items, 2)
            cursor.execute(
                "INSERT INTO order_items (item_id, order_id, product_name, price, is_return_eligible) VALUES (?, ?, ?, ?, ?)",
                (i_id, o_id, fake.catch_phrase(), price, random.choice([0, 1]))
            )

        # Generate shipment for the order
        tracking = f"TRK{fake.unique.random_number(digits=10)}"
        # Mostly delivered (70%), but 10% delayed, 10% transit, 5% damaged, 5% lost
        status = random.choices(STATUSES, weights=[70, 10, 10, 5, 5])[0] 
        
        cursor.execute(
            "INSERT INTO shipments (tracking_number, order_id, carrier, status, current_location, estimated_delivery) VALUES (?, ?, ?, ?, ?, ?)",
            (tracking, o_id, random.choice(CARRIERS), status, fake.city(), str(order_date + timedelta(days=random.randint(2, 7))))
        )

    conn.commit()
    conn.close()
    print("Data generation complete!")

if __name__ == "__main__":
    generate_data()
