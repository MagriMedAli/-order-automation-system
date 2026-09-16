# AI WhatsApp Order Automation

An AI-powered WhatsApp ordering system that turns natural-language customer messages into real orders.

Built with **n8n, Google Gemini, FastAPI, PostgreSQL, and the WhatsApp Cloud API**, the system connects the entire ordering process — from receiving a customer's message to validating products, managing customers, creating the order, and sending a confirmation back through WhatsApp.

---

## What It Does

Customers can interact with the business naturally through WhatsApp.

They can:

- Place orders using normal language
- Ask for the available product catalog
- Order multiple products in a single message
- Use different ways of expressing quantities
- Get automatic product availability checks
- Order without manually registering first

### Example

**Customer**

> I want 2 keyboards and a mouse

**AI**

Understands the request and converts it into structured order data.

**System**

- Identifies the products
- Checks availability
- Finds the customer
- Creates the customer if necessary
- Builds the order
- Stores it in PostgreSQL
- Calculates the total

**WhatsApp**

> Order confirmed!  
> Order #32  
> Total: 160 TND

No manual processing is required.

---

## Architecture

```text
                     WhatsApp Customer
                            │
                            ▼
                  WhatsApp Cloud API
                            │
                            ▼
                         n8n
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       Message Extraction          Product Retrieval
              │                           │
              └─────────────┬─────────────┘
                            ▼
                     Google Gemini
                            │
                    Intent Detection
                            │
              ┌─────────────┴─────────────┐
              │                           │
           Catalog                      Order
              │                           │
              ▼                           ▼
      Product Catalog            Availability Check
                                      │
                                      ▼
                                Product Matching
                                      │
                                      ▼
                                Customer Lookup
                                  /         \
                                 /           \
                              Existing       New
                                 │            │
                                 │      Create Customer
                                 │            │
                                 └─────┬──────┘
                                       ▼
                                  Build Order
                                       │
                                       ▼
                                  FastAPI API
                                       │
                                       ▼
                                  PostgreSQL
                                       │
                                       ▼
                              WhatsApp Confirmation