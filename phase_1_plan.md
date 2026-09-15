# Phase 1: Data & Environment Setup (Implementation Plan)

Yahan humara Phase 1 ka detailed plan hai. Jaisa aapne kaha, hum har phase se pehle ek clear plan banayenge aur us par discussion karenge.

## 1. Database & Schema (SQLite)

Kyunke yeh ek mock e-commerce system hai, hum **SQLite** use karenge. Yeh lightweight hai aur kisi complex setup ki zaroorat nahi. 

Humein 4 main tables banani chahiye:
* **Customers:** `customer_id`, `name`, `email`, `loyalty_status` (Bronze, Silver, Gold), `account_created`.
* **Orders:** `order_id`, `customer_id`, `order_date`, `total_amount`, `payment_status` (Paid, Refunded, Pending).
* **Order_Items:** `id`, `order_id`, `item_name`, `price`, `is_return_eligible` (Boolean).
* **Shipments:** `tracking_number`, `order_id`, `carrier` (FedEx, UPS), `status` (In Transit, Delivered, Delayed, Damaged), `current_location`, `estimated_delivery`.

## 2. Synthetic Data Generation

Hum ek Python script (`generate_mock_data.py`) likhenge jo `Faker` library use kar ke is database mein:
* 50 fake customers
* 100+ fake orders (jin mein kuch naye, kuch purane, aur kuch delayed/damaged hon) dalegi.

## 3. Policy Documents (For RAG)

AI ko support rules sikhane ke liye humein 2-3 text (Markdown) files banani hongi:
1. **`shipping_policy.md`:** (e.g., standard shipping takes 3-5 days, delayed packages get a 10% refund).
2. **`refund_policy.md`:** (e.g., returns allowed within 30 days of delivery, damaged items fully refunded).
3. **`faq.md`:** (General questions).

## 4. Test Scenarios

Hum kuch test questions pehle se define kar lenge takay baad mein agent ko test kar sakein. For example:
1. *Scenario 1 (Easy):* "Mera order #1234 kahan hai?" (Agent should look up shipping status).
2. *Scenario 2 (Complex):* "Mera package damaged aya hai, mujhe refund chahiye." (Agent should check policy, then escalate to human).
3. *Scenario 3 (Policy):* "Refund kitne dino mein wapis aata hai?" (Agent should read FAQ/Policy).

---

## Open Questions / Aapki Feedback Chahiye

> [!CAUTION]
> 1. **Database Schema:** Kya yeh 4 tables (Customers, Orders, Items, Shipments) kaafi hain ya kuch aur add karna chahiye?
> 2. **Dev Environment:** Kya aap chahte hain ke hum aik `requirements.txt` file banayen aur virtual environment setup ki instructions bhi likhein?
> 3. **Data Script:** Kya hum data generation script khud likhein ya aap uski vibe-coding karna chahenge (kyunke yeh core AI logic nahi hai)?
