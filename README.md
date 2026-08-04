<img width="1536" height="1024" alt="b0a888fe-ebea-466a-a5ca-da07d6c22475" src="https://github.com/user-attachments/assets/100860b1-d587-4c03-8737-42012bf802f5" />

# MissionCart

> AI Procurement Agent that transforms natural-language purchase goals into optimized Bills of Materials using multi-step reasoning, real product discovery, and conversational SMS.

---

## Overview

MissionCart is an agentic commerce system built for the Prava Agentic Commerce Hackathon.

Instead of asking users to manually browse products, compare specifications, check compatibility, and calculate budgets, MissionCart performs the entire procurement workflow autonomously.

A user simply describes an objective.

> "Build me a gaming PC under ₹80,000"

MissionCart plans the task, searches real merchant inventories, evaluates tradeoffs, optimizes the final build, explains every recommendation, and prepares the purchase flow—all through SMS.

---

## Architecture

```
                User
                 │
                 │ SMS
                 ▼
          Linq Messaging API
                 │
                 ▼
        Flask Webhook Server
                 │
                 ▼
       Intent Understanding (OpenAI)
                 │
                 ▼
      Procurement Planning Agent
                 │
        Generates Search Queries
                 │
                 ▼
          Prava CLI Search
                 │
      Multiple Merchant Results
                 │
                 ▼
    Procurement Architect Agent
                 │
 Compatibility • Budget • Performance
                 │
                 ▼
      Optimized Bill of Materials
                 │
                 ▼
      Conversational SMS Delivery
                 │
                 ▼
        Purchase Confirmation
```

---

# Features

## Goal-Based Procurement

Users never search for products directly.

Instead they describe an end objective:

- Gaming PC
- Home office
- Streaming setup
- Photography kit
- College workstation
- etc.

MissionCart decomposes that objective into procurement tasks.

---

## Multi-Step Agentic Reasoning

The system performs multiple reasoning stages:

1. Intent Analysis
2. Context Collection
3. Procurement Planning
4. Merchant Discovery
5. Technical Evaluation
6. Compatibility Verification
7. Budget Optimization
8. Final Recommendation
9. Purchase Flow

Each stage is performed independently rather than asking a single LLM to generate everything at once.

---

## Technical Procurement

Unlike recommendation engines, MissionCart reasons across multiple components simultaneously.

Examples include:

- CPU ↔ Motherboard compatibility
- PSU power requirements
- GPU bottlenecks
- Memory standards
- Budget allocation
- Upgrade paths

Recommendations are evaluated as complete systems rather than isolated products.

---

## Live Reasoning Stream

Instead of waiting 40–60 seconds for a final answer, MissionCart streams intermediate reasoning such as:

```

🧠 Evaluating GPU bottlenecks...

🧠 Prioritizing airflow before aesthetics...

🧠 Searching for AM5 motherboards...

🧠 Optimizing power efficiency...

```

This keeps long-running workflows transparent.

---

## Procurement Architecture

The final response includes

- Optimized BOM
- Budget utilization
- Component synergy
- Technical explanations
- Overall verdict
- Purchase confirmation flow

---

# Workflow

```
Receive SMS
      │
      ▼
Understand Intent
      │
      ▼
Ask Clarifying Questions
      │
      ▼
Generate Procurement Plan
      │
      ▼
Search Products via Prava
      │
      ▼
Collect Candidate Products
      │
      ▼
Evaluate Compatibility
      │
      ▼
Optimize Budget
      │
      ▼
Generate Final BOM
      │
      ▼
Deliver over SMS
      │
      ▼
Purchase
```

---

# Tech Stack

### Backend

- Python
- Flask
- Threaded Background Workers

### AI

- OpenAI GPT-4o
- GPT-4o-mini

### Commerce

- Prava CLI
- Merchant Discovery
- Product Search

### Messaging

- Linq SMS API

---

# Engineering Highlights

## Asynchronous Architecture

Webhook requests immediately acknowledge incoming messages while spawning background worker threads for long-running procurement workflows.

This prevents webhook retries while allowing complex reasoning pipelines.

---

## Multi-Agent Design

MissionCart separates responsibilities across specialized AI agents:

- Concierge
- Intent Analyzer
- Procurement Planner
- Procurement Architect

Each performs a dedicated reasoning task.

---

## Stateless Commerce Pipeline

```
Goal
 ↓
Planning
 ↓
Search
 ↓
Reasoning
 ↓
Optimization
 ↓
Recommendation
```

Each stage can be independently improved or replaced.

---

# Example

User

```
Build me a gaming PC under ₹80,000.
```

MissionCart

```
Mission Locked.

Searching compatible CPUs...

Searching GPUs...

Evaluating motherboard compatibility...

Optimizing performance per rupee...

━━━━━━━━━━━━━━

CPU
Ryzen 5 7600

GPU
RTX 4060

Motherboard
B650M

RAM
32GB DDR5

Total
₹79,842

Verdict

Excellent 1080p / 1440p gaming build with
strong upgrade path and balanced power delivery.

Reply BUY to continue.
```

---

# Future Work

- Multi-merchant checkout
- Live inventory updates
- Price tracking
- Dynamic re-optimization
- Persistent procurement memory
- Multi-turn procurement sessions
- Delivery tracking
- Post-purchase support

---

# Built For

Prava Agentic Commerce Hackathon 2026

Using

- OpenAI
- Prava
- Linq
- Python
- Flask
