# Reliable Assistive Technology Automation Tool

### A closed-loop, semantic UI automation system for real desktops

---

## What this is

This project is a **semantic, self-verifying desktop automation system**.

It doesn’t replay macros.  
It doesn’t scrape pixels.  
It doesn’t blindly trust a model.  
It doesn’t hardcode selectors.

It continuously *observes the real UI*, feeds that live state into a local language model, and uses the model’s output to drive system automation — while verifying every step against what the UI actually does.

This is not automation glued on top of a model.

This is a **model operating inside a live semantic UI feedback loop**.

---

## What it actually does

At runtime, the system:

1) Builds a live tree of **all interactive UI elements** currently visible on screen  
   (using real accessibility data — not brittle selectors)

2) Tracks the **currently active (focused) element** in real time

3) Feeds the full semantic UI state into a **local language model**  
   *(llama3.2-3b-instruct)*

4) Parses the model’s output into concrete system actions

5) Executes those actions

6) Observes the UI again

7) Repeats

Every step is validated against the actual UI state.

If the model tries to type into the wrong field, clicks the wrong element, or misinterprets the interface — the next UI snapshot exposes the mistake immediately.

This is not blind automation.

This is **semantic, closed-loop control**.

---

## Why this is different

Most automation systems fail because they are:

- geometry-based  
- selector-based  
- macro-based  
- assumption-based  
- one-shot  
- non-verifying  

They click and hope.

This system doesn’t.

It continuously sees:

- what elements exist  
- which one is focused  
- what text is actually present  
- what role each element plays  
- how the UI changes after each action  

The model is not guessing into a void.

It is operating against a live, semantic representation of the real UI.

---

## The reliability story

This system is **infrastructure-reliable**.

All unreliability comes from the model — not from the UI layer.

Why?

Because:

- It never assumes where elements are  
- It never assumes what has focus  
- It never assumes text was entered  
- It never assumes a click succeeded  
- It never assumes the UI state is what it expects  

Every action is followed by a fresh UI read.

The model can:

- inspect what it just typed  
- detect if focus moved unexpectedly  
- notice if a field didn’t update  
- recover from wrong actions  
- adapt to layout changes  

This is not brittle automation.

It is **self-correcting semantic automation**.

---

## What this enables

This is not a macro tool.

This is a foundation layer for:

- intelligent desktop agents  
- assistive technology automation  
- semantic UI automation  
- accessibility-aware control  
- context-aware system interaction  
- cross-application workflows  
- browser + desktop coordination  
- automation that survives UI changes  
- automation that can verify its own actions  

The model isn’t just issuing commands.

It is reasoning over the actual UI state.

---

## Why a local model matters

This system runs on a **local** language model:

**llama3.2-3b-instruct**

That means:

- no cloud dependency  
- no API costs  
- no data exfiltration  
- no network latency  
- no rate limits  
- no privacy risk  

The model runs entirely inside the same feedback loop as the UI.

The UI state is the ground truth.

---

## What this is not

This is **not**:

- a macro recorder  
- a pixel-matching tool  
- a web scraper  
- a DOM selector system  
- a browser automation framework  
- a brittle RPA script  
- a one-shot LLM wrapper  
- an AI demo toy  

It is a **semantic, event-driven automation substrate**.

---

## Scope and philosophy

This system is intentionally:

- scoped  
- deterministic  
- event-driven  
- feedback-based  
- accessibility-first  
- model-agnostic  
- infrastructure-reliable  

It does not pretend UI automation is easy.

It does not fake robustness.

It does not rely on fragile hacks.

It exposes the real UI state and forces the model to operate inside reality.

---

## Rough technical overview

- Builds a semantic tree of all interactive UI elements on screen  
- Tracks the currently active element in real time  
- Normalizes element identity across applications  
- Feeds live UI state into a local LLM  
- Parses model output into system actions  
- Executes actions  
- Re-reads the UI  
- Repeats continuously  

This is a closed-loop system.

Not a command generator.

---

## Why this exists

Because current automation tools are blind.

Because macro tools collapse under UI changes.

Because selector-based systems rot.

Because pixel matching is fragile.

Because accessibility APIs already expose the right data — nobody connected them to a model properly.

Because models shouldn’t operate in a vacuum.

Because automation should verify itself.

---

## Bottom line

This project turns the desktop into a **semantic, live-feedback environment** that a local language model can actually reason about.

Not a coordinate grid.  
Not a pixel buffer.  
Not a brittle DOM dump.  
Not a one-shot instruction prompt.

A real-time, closed-loop automation system that:

- sees what exists  
- knows what’s focused  
- reads what’s on screen  
- verifies every action  
- adapts to UI changes  
- and never assumes success.

That layer does not exist as a usable tool.

This builds it.

Works only on X11 desktop environments and the firefox browser, provided all dependencies are correctly installed. Change env.json for your environment variables. These are applications that the AI model is allowed to access.

WARNING: This relies on a text generation AI model that is fragile by nature. Use at your own risk.