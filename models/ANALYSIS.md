# Behavioral Framework Analysis

## Overview

This analysis documents the design problems and friction points in Mesa that the behavioral framework experiments are designed to expose through three targeted behavioral models.

---

## Model 01: Market Auction

**Problem Domain:** Request-Reply Interaction Patterns

**Goal:** Expose friction in Mesa when implementing request-reply interactions between agents.

**Design:**

- One Seller agent posts a reserve price every round.
- Eight Buyer agents with random budgets submit bids.
- Seller selects the highest valid bid and executes one sale per round.
- Communication is implemented using a shared inbox workaround.

**Problem Exposed:**
Mesa lacks built-in support for asynchronous request-reply message passing. The current implementation uses a shared inbox as a workaround, which is:

- Not composable (each model pair requires custom implementation)
- Fragile (no type safety or scheduling guarantees)
- Not observable (no built-in message tracing or debugging support)

**Reference:** [README.md](behavioral_experiment/01_market_auction/README.md)

---

## Model 02: Needs-Driven Wolf-Sheep

**Problem Domain:** Behavior Selection Under Competing Drives

**Goal:** Show friction in behavior selection when internal drives compete in a step-coupled policy.

**Design:**

- Extends baseline wolf-sheep model with sheep internal drives (hunger, fear, fatigue).
- Sheep select one action per step using priority rules:
  - flee if fear > 4
  - forage if energy < 3
  - rest if fatigue > 15
  - otherwise wander
- Wolves and grass remain close to baseline behavior.

**Problem Exposed:**
Mesa's action scheduling system is designed for single-action execution. It becomes unclear how to represent:

- Mutually exclusive behavior states within a single step
- Priority-based decision trees that run before action execution
- Internal state tracking (drives) that influences scheduling

The model currently solves this with custom step logic, but this is not composable across different behavioral models.

**Reference:** [README.md](behavioral_experiment/02_needs_driven_wolf_sheep/README.md)

---

## Model 03: Opinion Diffusion Network

**Problem Domain:** Multi-Agent Communication and Signaling

**Goal:** Expose communication friction in Mesa signals and pub-sub workflows for networked multi-agent interaction.

**Design:**

- Agents have opinions in [0.0, 1.0] placed on an Erdos-Renyi graph.
- Each step, every agent broadcasts its current opinion.
- Neighbors update opinion by attraction or contrarian repulsion.
- Signaling uses Observable and ObservableList from mesa_signals.

**Problem Exposed:**
Mesa lacks a unified pub-sub pattern for agent communication. The current mesa_signals approach requires:

- Explicit subscription/unsubscription management
- Manual lifetime management (when do subscriptions end?)
- No built-in routing or filtering of messages
- Difficult to implement multicast patterns (one-to-many broadcasts)

**Reference:** [README.md](behavioral_experiment/03_opinion_diffusion/README.md)

---

## Design Thesis

These three models target orthogonal communication and behavior problems:

1. **Synchronous RPC** (Market Auction): How do agents make requests and wait for replies?
2. **Internal State Management** (Wolf-Sheep): How do internal drives influence action scheduling?
3. **Asynchronous Pub-Sub** (Opinion Diffusion): How do agents broadcast and subscribe to multi-agent signals?

The hypothesis is that Mesa's core abstraction (model.step() → agent.step() → action) lacks declarative support for these patterns, forcing users to implement ad-hoc solutions.

---

## Test Stability Notes

Date: March 30, 2026

### Mesa Test Stability Notes

---

Mesa Test Stability Notes

Date: March 30, 2026

Scope:

    Document the changes made in Mesa test files, the failures encountered while validating them, and the exact fixes or workarounds used.

Files Changed:

    mesa/tests/experimental/test_actions_interruption.py

    mesa/tests/examples/test_examples_viz.py

1. Action interruption test cleanup

Problem:

    Several tests in `test_actions_interruption.py` manually set `action._event = None` after mutating `action._progress`.

    That pattern does not actually cancel the scheduled event in the model scheduler. It only drops the Python reference held by the action object. The underlying scheduled completion event can remain in the scheduler and fire later if model time advances.

Why this was risky:

    The tests could become brittle or misleading because they bypassed the public action lifecycle. They were asserting interruption and cancellation behavior without actually cleaning up scheduled events through the scheduler.

Change made:

    Replaced direct `_event = None` manipulation with real time advancement using `model.run_for(...)`.

    Then called `interrupt()` or `cancel()` through the action API so the event is cancelled through the normal `_cancel_event()` path.

Updated patterns:

    `model.run_for(5.0)` before `action.interrupt()` for the 50 percent progress case.

    `model.run_for(3.0)` before interruption for the resume-progress case.

    `model.run_for(7.0)` before `action.cancel()` for cancellation progress.

    `model.run_for(4.0)`, `model.run_for(2.5)`, and `model.run_for(12.0)` for progress, remaining time, and elapsed time assertions.

Additional cleanup:

    Removed the unnecessary `# type: ignore` from the `import pytest` line.

    Renamed a few unused `model` bindings to `_model` to keep the tests clean where the model variable was not directly referenced after construction.

Verification:

    Ran:

        `E:\GSoC-learning-space\.venv\Scripts\python.exe -m pytest E:\GSoC-learning-space\mesa\tests\experimental\test_actions_interruption.py`

    Result:

        23 tests passed.

    Warning observed:

        `PytestCacheWarning` related to `.pytest_cache` on Windows. This did not affect the test result.

2. Visualization test flake in CI

CI failure observed:

    The full test suite failed in `tests/examples/test_examples_viz.py::test_pd_grid_model[chromium]`.

Error:

    `playwright._impl._errors.Error: Locator.screenshot: Element is not attached to the DOM`

Where it happened:

    The failure occurred during screenshot capture of an `img` locator inside `run_model_test(...)`.

Root cause:

    The visualization test was taking screenshots directly from `page_session.locator("img")`, `.first`, or `.last`.

    In the Solara/Playwright rendering flow, the `img` node can be replaced during rerender. If that happens between locator resolution and the actual screenshot capture, Playwright reports that the element is no longer attached to the DOM.

Why this is unrelated to the interruption test change:

    The failing test was in the visualization suite, not in `test_actions_interruption.py`.

    The interruption tests passed independently.

    The failure pattern is consistent with a frontend rerender race, not with action scheduling logic.

Change made:

    Added a helper named `take_stable_screenshot(locator, retries=3)` in `test_examples_viz.py`.

    This helper:

        waits for the locator to be visible

        attempts `locator.screenshot()`

        catches Playwright errors only when the message contains `Element is not attached to the DOM`

        retries a few times before re-raising the last error

    Replaced direct screenshot calls in `run_model_test(...)` with `take_stable_screenshot(...)` for:

        the initial space image

        the initial graph image

        the updated space image

        the updated graph image

Goal of the change:

    Keep the test intent exactly the same while making it resilient to harmless DOM replacement during Solara rerenders.

3. Local verification problems and how they were handled

Issue A: `pytest` missing from the repo venv

Problem:

    Initial local test runs failed because `pytest` was not installed in `E:\GSoC-learning-space\.venv`.

What happened:

    `uv pip install pytest` had been run from another directory and installed into:

        `E:\GSoC-learning-space\models\behavioral_experiment\.venv`

    But the actual test command used:

        `E:\GSoC-learning-space\.venv\Scripts\python.exe`

Fix:

    Installed `pytest` directly into the repo venv.

Outcome:

    The focused action interruption test file then ran successfully.

Issue B: stale Git lock blocked commit attempts

Problem:

    `git commit` failed with:

        `Unable to create '.../.git/index.lock': File exists`

Diagnosis:

    Checked active `git` processes and the lock file.

    The lock file was zero bytes and the previously reported Git process IDs were no longer alive.

Conclusion:

    The lock was stale rather than belonging to an active Git operation.

Fix:

    Removed `.git/index.lock`.

Outcome:

    The repository became writable for Git operations again.

Issue C: local viz test initially failed because Playwright was not installed

Problem:

    Running the targeted visualization test failed during collection with `ModuleNotFoundError: No module named 'playwright'`.

Fix:

    Installed Mesa dev dependencies into `E:\GSoC-learning-space\.venv` using editable install with `[dev]` extras.

Outcome:

    The environment then contained `playwright`, `pytest-playwright`, `solara`, `ipywidgets`, `matplotlib`, and related dependencies.

Issue D: pytest plugin resolution was polluted by another virtual environment

Problem:

    Even after installing the correct dependencies into the repo venv, running the targeted visualization test still imported `pytest_playwright` from:

        `E:\GSoC-learning-space\models\behavioral_experiment\.venv`

    That environment had an incompatible Playwright/greenlet combination, producing:

        `ModuleNotFoundError: No module named 'greenlet._greenlet'`

Why this was confusing:

    Plain imports from the repo interpreter showed the correct modules resolving from:

        `E:\GSoC-learning-space\.venv\Lib\site-packages`

    But pytest startup and plugin loading still picked up the plugin from the other environment.

Mitigations attempted:

    Set:

        `PYTHONNOUSERSITE=1`

        `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`

    Explicitly enabled only:

        `solara.test.pytest_plugin`

        `pytest_playwright.pytest_playwright`

    Verified the correct pytest plugin entry-point names.

    Verified the repo venv could directly import:

        `pytest_playwright.pytest_playwright`

        `solara.test.pytest_plugin`

Next workable approach:

    Use a small Python bootstrap script that:

        strips any `behavioral_experiment\.venv` entries from `sys.path`

        imports `pytest`, `solara.test.pytest_plugin`, and `pytest_playwright.pytest_playwright` directly

        calls `pytest.main(...)` with those already-imported plugin modules

Status:

    This path was prepared, but the full targeted Playwright verification was interrupted before completion.

4. Current state

Implemented changes:

    `test_actions_interruption.py` now uses real model time advancement and public interruption/cancellation behavior instead of nulling `_event`.

    `test_examples_viz.py` now retries screenshots when DOM replacement detaches the target `img` element during rerender.

Fully verified:

    `test_actions_interruption.py`

Partially verified / prepared but not completed locally:

    `test_examples_viz.py::test_pd_grid_model`

Recommended next verification command:

    Run the Playwright test through a bootstrap script that forces pytest to use plugins from `E:\GSoC-learning-space\.venv` only, avoiding plugin leakage from `models\behavioral_experiment\.venv`.
