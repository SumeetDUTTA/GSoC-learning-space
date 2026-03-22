from __future__ import annotations

import networkx as nx
from mesa import Model
from mesa.discrete_space import Network

from agents import OpinionAgent


class OpinionDiffusionModel(Model):
    """Opinion diffusion on a graph using mesa_signals-based broadcasting."""

    def __init__(
        self,
        num_agents: int = 15,
        avg_degree: int = 4,
        learning_rate: float = 0.1,
        contrarian_probability: float = 0.2,
        rng=None,
    ):
        super().__init__(rng=rng)
        self.round = 0

        edge_probability = min(1.0, avg_degree / max(1, num_agents - 1))
        graph = nx.erdos_renyi_graph(
            num_agents, edge_probability, seed=self.random.randint(0, 10**9)
        )
        while num_agents > 1 and not nx.is_connected(graph):
            graph = nx.erdos_renyi_graph(
                num_agents, edge_probability, seed=self.random.randint(0, 10**9)
            )

        self.network = Network(graph, capacity=1, random=self.random)

        for cell in self.network.all_cells:
            OpinionAgent(
                self,
                cell=cell,
                opinion=self.random.uniform(0.0, 1.0),
                learning_rate=learning_rate,
                contrarian_probability=contrarian_probability,
            )

        for agent in self.agents_by_type[OpinionAgent]:
            agent.connect_signal_subscriptions()

        self.history: list[dict] = []
        self._log_round()

    def _log_round(self) -> None:
        opinions = [agent.opinion for agent in self.agents_by_type[OpinionAgent]]
        if not opinions:
            return

        self.history.append(
            {
                "round": self.round,
                "mean_opinion": sum(opinions) / len(opinions),
                "min_opinion": min(opinions),
                "max_opinion": max(opinions),
            }
        )

    def step(self) -> None:
        self.round += 1
        self.agents_by_type[OpinionAgent].shuffle_do("step")
        self._log_round()
