# Checkout Sequence (Readable)

This file explains the checkout flow in plain steps and includes the Mermaid sequence diagram.

## Plain steps

1. User adds product(s) to their cart via the web UI (`/cart/add`).
2. The server updates or creates `CartItem` records in the database.
3. User submits checkout (`/checkout`).
4. Server creates an `Order` and corresponding `OrderItem` rows, and may reserve stock.
5. Server calls the payment gateway API to process payment.
6. On success: update `Order` status to paid/processing, decrement product stock, send confirmation email/SMS.
7. On failure: set payment status to failed and notify the user.

## Mermaid (sequence)

```mermaid
sequenceDiagram
  participant U as Browser/User
  participant S as vendora (Django)
  participant CART as Cart Service
  participant DB as Database
  participant PAY as PaymentGateway
  participant MAIL as Email/SMS

  U->>S: Add product to cart (POST /cart/add)
  S->>DB: create/update CartItem
  DB-->>S: Cart updated
  U->>S: Checkout (POST /checkout)
  S->>DB: create Order and OrderItems, reserve stock
  DB-->>S: Order created
  S->>PAY: initiate payment (API)
  PAY-->>S: payment result
  alt payment success
    S->>DB: update Order.payment_status='paid', status='processing'
    S->>DB: decrement Product.stock_quantity, increment Product.total_sold
    S->>MAIL: send order confirmation
    MAIL-->>U: confirmation email/SMS
  else payment failed
    S->>DB: update Order.payment_status='failed'
    S->>U: show payment failure
  end
```
