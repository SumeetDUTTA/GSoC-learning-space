from __future__ import annotations
from dataclasses import dataclass

from mesa import Agent

@dataclass
class Bid:
    buyer: "Buyer"
    amount: float

class Buyer(Agent):
    def __init__(self, model, budget: float):
        super().__init__(model)
        self.budget = budget
        self.item_won = 0

    def step(self) -> None:
        if self.budget <= 0:
            return

        seller = self.model.seller
        floor = max(0.0, seller.current_price * 0.5)
        if self.budget < floor:
            return
        
        offer = self.random.uniform(floor, self.budget)
        # Workaround friction point: direct append into seller shared inbox
        seller.inbox.append(Bid(buyer=self, amount=offer))

class Seller(Agent):
    def __init__(self, model, price:float):
        super().__init__(model)
        self.price = price
        self.current_price = price
        self.inbox: list[Bid] = []
        self.items_sold = 0
        self.total_revenue = 0.0
        self.last_sale_price: float | None = None
        self.last_winner_id: int | None = None

    def post_price(self) -> None:
        # Keeping it simple: seller posts the same reserved price every round.
        self.current_price = self.price

    def step(self) -> None:
        winning_bid: Bid | None = None
        if self.inbox:
            winning_bid = max(self.inbox, key=lambda b: b.amount)
          
        if winning_bid and winning_bid.amount >= self.current_price:
            if winning_bid.buyer.budget >= winning_bid.amount:
                # Processing the sale
                winning_bid.buyer.budget -= winning_bid.amount
                winning_bid.buyer.item_won += 1
                self.items_sold += 1
                self.total_revenue += winning_bid.amount
                self.last_sale_price = winning_bid.amount
                self.last_winner_id = winning_bid.buyer.unique_id
            else:
                self.last_sale_price = None
                self.last_winner_id = None
        else:
            self.last_sale_price = None
            self.last_winner_id = None
        
        # Workaround friction point: we manually clear the shared inbox each round
        self.inbox.clear()