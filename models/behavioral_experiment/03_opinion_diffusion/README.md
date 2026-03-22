# Model 03 - Opinion Diffusion Network (Days 7-8)

## Goal

Show communication friction in the current Mesa signals/pub-sub layer for multi-agent network interactions.

## Model Summary

- Each agent has an opinion value in [0.0, 1.0].
- Agents live on a graph (Network discrete space).
- Each step, every agent broadcasts its current opinion.
- Neighboring agents update their opinion either:
  - toward the received opinion (attraction), or
  - away from it (repulsion / contrarian behavior).

## What Was Implemented

### 1) Agent state

- Opinion is represented by an Observable field on OpinionAgent.
- A broadcasts ObservableList is used as the signaling channel.

### 2) Subscription wiring

- During model initialization, each agent subscribes to APPENDED events of each neighbor's broadcasts list.
- Subscription handler reads message payload and updates the receiver's opinion.

### 3) Broadcast on each step

- On step, each agent appends a message object to broadcasts.
- The append event triggers neighbor handlers through mesa_signals.

## Why This Exposes Gaps

This works, but the communication layer has friction for larger or more structured protocols:

- No topic-based filtering:
  every subscriber to the same ObservableList signal receives all messages for that signal.
- No ordering guarantee:
  update order depends on execution sequence and callback timing, not an explicit global message order.
- No wildcard subscription for network topics/channels:
  subscriptions are attached per observable on a specific emitter; there is no global topic wildcard across agents/channels for communication workflows.

## What a Cleaner API Could Look Like

Examples of APIs that would reduce manual wiring:

- publish(topic="opinion", payload=...)
- subscribe(topic="opinion", filter=..., handler=...)
- wildcard subscribe(topic="opinion.*", handler=...)
- ordered delivery modes (fifo, causal, timestamp-based)
- acknowledgements / retry hooks for robust protocols

## How to Run

~~~python
from model import OpinionDiffusionModel

m = OpinionDiffusionModel(num_agents=20, avg_degree=5, learning_rate=0.1)
for _ in range(10):
  m.step()

print("Rounds:", m.round)
print("Last summary:", m.history[-1])
~~~

## Notes

- Because updates are event-driven while agents are activated sequentially, opinions can change within the same round before all agents have broadcast.
- This behavior is useful to illustrate the current absence of explicit message scheduling semantics.
