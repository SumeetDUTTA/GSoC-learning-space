from __future__ import annotations

from mesa.discrete_space import FixedAgent
from mesa.experimental.mesa_signals import (
    HasEmitters,
    ListSignals,
    Observable,
    ObservableList,
)


class OpinionAgent(FixedAgent, HasEmitters):
    """Network agent that updates beliefs from neighbor broadcasts."""

    opinion = Observable(0.5)
    broadcasts = ObservableList()

    def __init__(
        self,
        model,
        cell,
        opinion: float,
        learning_rate: float,
        contrarian_probability: float,
    ):
        super().__init__(model)
        self.cell = cell
        self.opinion = opinion
        self.learning_rate = learning_rate
        self.contrarian_probability = contrarian_probability
        self.broadcasts = []
        self.messages_received = 0

    def on_neighbor_broadcast(self, message) -> None:
        payload = message.additional_kwargs["new"]
        sender_id = payload["sender_id"]
        neighbor_opinion = payload["opinion"]

        if sender_id == self.unique_id:
            return

        self.messages_received += 1

        if self.random.random() < self.contrarian_probability:
            updated = self.opinion - self.learning_rate * (
                neighbor_opinion - self.opinion
            )
        else:
            updated = self.opinion + self.learning_rate * (
                neighbor_opinion - self.opinion
            )

        # Keep values in [0, 1] after attraction/repulsion updates.
        self.opinion = min(1.0, max(0.0, updated))

    def connect_signal_subscriptions(self) -> None:
        """Subscribe to neighbor broadcast events."""
        for neighbor in self.cell.neighborhood.agents:
            neighbor.observe(
                "broadcasts", ListSignals.APPENDED, self.on_neighbor_broadcast
            )

    def step(self) -> None:
        self.broadcasts.append(
            {
                "step": int(self.model.time),
                "sender_id": self.unique_id,
                "opinion": self.opinion,
            }
        )
