# Etsy Order Notifier
 
A small internal tool that listens for Etsy's `order.paid` webhook and sends an email notification whenever a buyer completes a purchase in my shop.
 
## What it does
 
1. Receives a webhook POST from Etsy the moment an order is paid.
2. Verifies the request signature using the Etsy webhook signing secret.
3. Sends an email notification with the order details.
That's it — no dashboard, no inventory management, no other integrations.
 
## Stack
 
- Etsy Open API v3 (OAuth 2.0 with PKCE)
- Serverless function (webhook receiver)
- Transactional email service for sending notifications
## Status
 
Personal-use project, built and maintained for a single Etsy shop.
 
## Scopes used
 
- `transactions_r` — read order/receipt details
## Notes
 
This app is not public-facing and is not intended for use by other sellers or third parties.
