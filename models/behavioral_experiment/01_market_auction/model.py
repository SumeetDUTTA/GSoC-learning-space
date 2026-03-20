from __future__ import annotations
from mesa import Model

from agents import Buyer, Seller


class MarketAuctionModel(Model):
    def __init__(
        self,
        num_buyers: int = 8,
        seller_price: float = 40.0,
        min_budget: float = 20.0,
        max_budget: float = 120.0,
        rng=None,
    ):
        super().__init__(rng=rng)
        self.round = 0
        self.seller = Seller(self, price=seller_price)
        budgets = [self.random.uniform(min_budget, max_budget) for _ in range(num_buyers)]
        Buyer.create_agents(self, num_buyers, budgets)

        self.round_log: list[dict] = []

    def step(self) -> None:
        self.round += 1

        # 1) Seller posts the current price.
        self.seller.post_price()

        # 2) Buyers submit their bids(via shared inbox workaround).
        self.agents_by_type[Buyer].shuffle_do('step')

        # 3) Seller processes the highest valid bid.
        self.seller.step()

        self.round_log.append({
            'round': self.round,
            'seller_price': self.seller.current_price,
            'winning_bid': self.seller.last_sale_price,
            'winner_id': self.seller.last_winner_id,
            'items_sold_total': self.seller.items_sold,
            'revenue_total': self.seller.total_revenue,
        })
