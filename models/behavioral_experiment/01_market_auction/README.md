# Model 01: Market Auction

## Goal

This model exposes a friction point in Mesa when implementing a simple request-reply interaction:

- Buyer agent must send bids to the seller and the seller must decide a winner each round.

## Setup

- 1 `Seller` agent posts a reserve price each round
- 5-10 `Buyer` agents with random budgets submit bids each round
- The `Seller` accepts the highest valid bid, transform one item, then resets state for the next round.

## What was implemented (workaround pattern)

To implement request-reply, we used:

- Shared inbox on seller:
  seller.inbox is a list where buyers append bid messages
- Manual message object:
  Bid is a custom data object (not a Mesa Agent)
- Manual lifecycle:
  seller reads inbox, picks winner, applies transfer, then clears inbox

This is functional, but it is custom plumbing rather than first-class messaging.

## Friction point observed in Mesa

For this interaction style, Mesa currently lacks built-in APIs for:

- Typed message passing between agents
- Broadcast send to agent groups by type or filter
- Request-reply semantics with acknowledgement or timeout
- Mailbox delivery guarantees and ordering controls

Because these are missing, interaction protocols are hand-written in each model.

## What a clean API could look like

A cleaner API might support primitives like:

- send message:
  buyer.send(to=seller, msg=Bid(amount=37.2))
- broadcast:
  seller.broadcast(to=Buyer, msg=AuctionOpened(price=40.0))
- request-reply:
  response = buyer.request(to=seller, msg=BidRequest(...), timeout=1.0)
- inbox handling:
  seller.on(Bid, handler=resolve_bid)
- acknowledgement:
  buyer.await_ack(message_id)

With these primitives, auction logic would become protocol-focused, instead of manually managing list mailboxes.

## Minimal run snippet

You can run a short simulation from a Python shell:

from model import MarketAuctionModel

m = MarketAuctionModel(num_buyers=8, seller_price=40.0)
for _ in range(10):
    m.step()

print("Sold:", m.seller.items_sold)
print("Revenue:", round(m.seller.total_revenue, 2))
print("Last round:", m.round_log[-1])
