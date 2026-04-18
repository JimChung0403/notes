# A Practical Guide to Building Agents

Source: OpenAI PDF, downloaded from the official CDN on April 15, 2026.

This Markdown file is a cleaned, structured rewrite of the original guide. It preserves the main ideas, examples, and recommendations in a format that is easier to read, search, and reuse in documentation workflows.

## Contents

- [Introduction](#introduction)
- [What Is an Agent?](#what-is-an-agent)
- [When Should You Build an Agent?](#when-should-you-build-an-agent)
- [Agent Design Foundations](#agent-design-foundations)
- [Selecting Models](#selecting-models)
- [Defining Tools](#defining-tools)
- [Configuring Instructions](#configuring-instructions)
- [Orchestration](#orchestration)
- [Single-Agent Systems](#single-agent-systems)
- [When to Create Multiple Agents](#when-to-create-multiple-agents)
- [Multi-Agent Systems](#multi-agent-systems)
- [Manager Pattern](#manager-pattern)
- [Decentralized Pattern](#decentralized-pattern)
- [Guardrails](#guardrails)
- [Human Intervention](#human-intervention)
- [Conclusion](#conclusion)
- [More Resources](#more-resources)

## Introduction

Large language models are now capable of handling increasingly complex, multi-step work. Improvements in reasoning, multimodal input handling, and tool use have enabled a new class of software systems: agents.

This guide is aimed at product and engineering teams building their first agent-based systems. It focuses on practical implementation choices rather than theory alone, covering:

- how to identify the right use cases for agents
- how to structure models, tools, and instructions
- how to choose orchestration patterns
- how to add guardrails so systems remain safe and predictable

The central message is straightforward: start with strong foundations, keep the architecture as simple as possible, and evolve based on real usage and evaluation data.

## What Is an Agent?

Traditional software helps users execute workflows. Agents go further: they execute workflows on behalf of users with meaningful autonomy.

> Agents are systems that independently accomplish tasks on your behalf.

A workflow is any sequence of steps needed to achieve a user goal, such as:

- resolving a customer support issue
- booking a reservation
- making a code change
- generating a report

Not every LLM-powered product is an agent. A chatbot, a classifier, or a single-turn prompt-response application may use an LLM, but if it does not control workflow execution, it is not acting as an agent.

An agent typically has two defining properties:

1. It uses an LLM to manage decisions and workflow progression.
   The model decides what to do next, recognizes when a task is complete, and can sometimes recover from failure.
2. It uses tools to interact with external systems.
   The agent gathers information and performs actions through tools, always within defined constraints.

## When Should You Build an Agent?

Agents are most valuable when deterministic logic starts breaking down. They are especially useful for workflows that involve ambiguity, context-sensitive judgment, or large amounts of unstructured information.

The guide contrasts two approaches to fraud analysis:

- a rules engine behaves like a checklist
- an LLM agent behaves more like an experienced investigator that considers context, weak signals, and nuance

Good candidate use cases usually involve one or more of the following:

### 1. Complex decision-making

These are workflows with many exceptions, edge cases, or context-dependent judgments.

Example:

- deciding whether to approve a refund

### 2. Difficult-to-maintain rules

Some systems become hard to manage because the ruleset grows too large and too brittle.

Example:

- performing vendor security reviews with many branching conditions

### 3. Heavy reliance on unstructured data

Agents are well-suited to cases where inputs are documents, free text, or ongoing conversations rather than clean database records.

Example:

- processing a home insurance claim

If your workflow can be handled cleanly with deterministic logic, conventional automation may still be the better choice.

## Agent Design Foundations

At a minimum, an agent consists of three parts:

1. **Model**
   The LLM that performs reasoning and chooses actions.
2. **Tools**
   Functions, APIs, or system interfaces the agent can call.
3. **Instructions**
   The rules and operating guidance that shape the agent's behavior.

A minimal example in the Agents SDK looks like this:

```python
from agents import Agent

weather_agent = Agent(
    name="Weather agent",
    instructions="You are a helpful agent who can answer weather questions.",
    tools=[get_weather],
)
```

These three pieces matter more than any framework choice. You can implement the same design principles in the OpenAI Agents SDK, another agent framework, or your own orchestration layer.

## Selecting Models

Model selection is a tradeoff between capability, latency, and cost.

Not every step in a workflow needs the strongest model. A smaller and faster model may be enough for:

- retrieval
- classification
- simple routing

More capable models may be better for:

- nuanced decisions
- ambiguous reasoning
- safety-sensitive judgment calls

The guide recommends this process:

1. Build the first version with the strongest model available for each step.
2. Establish a baseline with evals.
3. Replace expensive steps with smaller models where quality remains acceptable.

In short:

- use evals to define the baseline
- optimize first for quality
- optimize second for cost and latency

## Defining Tools

Tools let agents interact with the outside world. They are the bridge between language-based reasoning and real execution.

Tools may connect to:

- APIs
- internal systems
- databases
- CRMs
- document stores
- web search
- UI automation systems for legacy software

The guide groups tools into three categories:

| Type | Purpose | Examples |
| --- | --- | --- |
| Data | Retrieve information needed for execution | query databases, read PDFs, search the web |
| Action | Make changes or trigger real operations | send emails, update CRM records, escalate tickets |
| Orchestration | Allow agents to call other agents | refund agent, research agent, writing agent |

Well-designed tools should be:

- standardized
- well-documented
- reusable
- thoroughly tested

This reduces duplication and makes tool selection easier for the agent.

Example:

```python
from agents import Agent, WebSearchTool, function_tool
import datetime

@function_tool
def save_results(output):
    db.insert({"output": output, "timestamp": datetime.datetime.now()})
    return "File saved"

search_agent = Agent(
    name="Search agent",
    instructions="Help the user search the internet and save results if asked.",
    tools=[WebSearchTool(), save_results],
)
```

As the tool surface grows, it can become useful to split capabilities across multiple agents.

## Configuring Instructions

Instructions are especially important in agent systems because the model is not just responding once; it is making ongoing decisions across a workflow.

Better instructions reduce ambiguity, improve consistency, and lower execution errors.

The guide recommends four instruction design practices.

### Use existing documents

Start from the operating procedures, support playbooks, or policy documents your team already uses. Convert them into agent-friendly instructions instead of inventing the workflow from scratch.

### Break tasks into smaller steps

Dense policy documents often become clearer and more reliable when rewritten as explicit steps the model can follow.

### Define clear actions

Each instruction should map to a concrete action or output. For example:

- ask the user for an order number
- call an account lookup API
- send a confirmation message

### Capture edge cases

Real conversations do not follow the happy path. Instructions should address missing information, unexpected questions, and conditional branches.

The guide also suggests using strong reasoning models to convert source documents into draft instructions automatically.

Example prompt:

```text
You are an expert in writing instructions for an LLM agent.
Convert the following help center document into a clear numbered list
of instructions for an agent. Remove ambiguity and phrase everything
as direct operational guidance.

Document:
{{help_center_doc}}
```

## Orchestration

Once the model, tools, and instructions are in place, the next design question is orchestration: how the system actually executes the workflow.

The guide recommends resisting the urge to build a highly autonomous, complex system immediately. Teams usually succeed faster by starting simple and introducing complexity only when it becomes necessary.

Two broad orchestration categories are highlighted:

1. **Single-agent systems**
2. **Multi-agent systems**

## Single-Agent Systems

A single agent can often handle a surprising amount of complexity if it has:

- well-defined tools
- strong instructions
- guardrails
- a run loop with clear exit conditions

Each additional tool extends the system without forcing an early move to multi-agent orchestration.

The underlying execution model is usually a loop:

1. the model examines the current state
2. it decides whether to respond, call a tool, or continue reasoning
3. the loop continues until an exit condition is met

Typical exit conditions include:

- final output produced
- no further tool call needed
- structured result returned
- error encountered
- max turns reached

Example:

```python
from agents import Runner, UserMessage

result = Runner.run(
    agent,
    [UserMessage("What's the capital of the USA?")],
)
```

The guide also recommends using prompt templates before moving to multiple agents. A strong template with variables is often easier to maintain than many separate prompts.

Example:

```text
You are a call center agent.
You are speaking with {{user_first_name}}, who has been a member for
{{user_tenure}}. Their most common complaint categories are
{{user_complaint_categories}}.

Greet the user, thank them for being a loyal customer, and answer
their questions.
```

## When to Create Multiple Agents

The default recommendation is to push a single agent as far as it can reasonably go before splitting the system.

Multiple agents can create clearer boundaries, but they also add:

- orchestration overhead
- more moving parts
- more places for failures to occur
- additional evaluation complexity

The guide gives two practical signals that a split may be warranted.

### 1. Complex logic

If a prompt becomes overloaded with conditional branches and large policy trees, separating responsibilities across agents may improve reliability.

### 2. Tool overload

The problem is not just tool count. It is usually tool similarity and overlap. Some agents can manage many distinct tools. Others fail with fewer tools if their purposes are too similar or poorly described.

Before splitting, try improving:

- tool naming
- parameter clarity
- tool descriptions

If performance still degrades, multiple agents may be the right move.

## Multi-Agent Systems

The guide focuses on two common patterns:

1. **Manager pattern**
2. **Decentralized handoff pattern**

In both cases, agents can be thought of as nodes in a graph:

- in the manager pattern, edges are tool calls
- in the decentralized pattern, edges are handoffs

The same design principles still apply:

- keep components modular
- keep prompts clear
- keep responsibilities well-defined

## Manager Pattern

In the manager pattern, a central agent coordinates specialized agents through tool calls.

This works well when you want:

- one agent to remain in control
- one place that sees the user directly
- centralized synthesis of results

Example use case:

- translating one phrase into several languages by calling separate language-specific agents

Illustrative example:

```python
from agents import Agent, Runner

manager_agent = Agent(
    name="manager_agent",
    instructions=(
        "You are a translation agent. Use the tools provided to translate. "
        "If the user asks for multiple translations, call the relevant tools."
    ),
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
        italian_agent.as_tool(
            tool_name="translate_to_italian",
            tool_description="Translate the user's message to Italian",
        ),
    ],
)

async def main():
    result = await Runner.run(
        manager_agent,
        "Translate 'hello' to Spanish, French and Italian for me!",
    )
    for message in result.new_messages:
        print(message.content)
```

The guide also notes a design difference between declarative and code-first frameworks.

### Declarative vs. non-declarative graphs

Some frameworks require developers to define all branches, loops, and edges up front. This can make workflows visually clear, but it often becomes cumbersome as systems grow more dynamic.

A code-first approach allows developers to express orchestration in normal program logic without predefining the entire graph.

## Decentralized Pattern

In the decentralized pattern, agents hand off workflow control to one another directly.

A handoff is not just a sub-call. It is a transfer of execution responsibility from one agent to another, usually along with the latest conversation state.

This works well when:

- no single agent needs to stay in charge
- specialists should interact with the user directly
- the workflow naturally shifts between domains

Example customer service setup:

```python
from agents import Agent, Runner

technical_support_agent = Agent(
    name="Technical Support Agent",
    instructions="Resolve technical issues, outages, and troubleshooting requests.",
    tools=[search_knowledge_base],
)

sales_assistant_agent = Agent(
    name="Sales Assistant Agent",
    instructions="Help customers browse products and complete purchases.",
    tools=[initiate_purchase_order],
)

order_management_agent = Agent(
    name="Order Management Agent",
    instructions="Handle order tracking, delivery schedules, returns, and refunds.",
    tools=[track_order_status, initiate_refund_process],
)

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "Act as the first point of contact and route the user to the correct "
        "specialized agent."
    ),
    handoffs=[
        technical_support_agent,
        sales_assistant_agent,
        order_management_agent,
    ],
)

await Runner.run(
    triage_agent,
    "Could you please provide an update on the delivery timeline for our recent purchase?",
)
```

In this example, the triage agent receives the user message first, determines it is about an order, and hands the interaction to the order management agent.

This pattern is particularly effective for:

- support triage
- multi-department workflows
- domain-specific conversations where specialists should take over fully

## Guardrails

Guardrails reduce safety, privacy, and reliability risks in agent systems.

Examples of risks include:

- prompt leakage
- jailbreak attempts
- policy violations
- unsafe content
- irreversible or sensitive tool use

The guide recommends layered defenses rather than reliance on a single protection mechanism.

Possible layers include:

- LLM-based classifiers
- moderation systems
- regex or blocklist filters
- input limits
- output validation
- tool-level approval logic

### Types of guardrails

| Guardrail | Purpose |
| --- | --- |
| Relevance classifier | flags off-topic inputs |
| Safety classifier | detects jailbreaks, prompt injection, or unsafe manipulation |
| PII filter | prevents unnecessary exposure of personal data |
| Moderation | catches harmful or inappropriate content |
| Tool safeguards | gate risky actions based on impact and reversibility |
| Rules-based protections | block known patterns such as banned terms or SQL injection |
| Output validation | checks responses for policy or brand alignment |

### Building guardrails

The recommended heuristic is:

1. Start with privacy and safety.
2. Add new guardrails when real failures reveal new risks.
3. Keep tuning the balance between user experience and security.

Example:

```python
from agents import (
    Agent,
    Guardrail,
    GuardrailFunctionOutput,
    GuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from pydantic import BaseModel

class ChurnDetectionOutput(BaseModel):
    is_churn_risk: bool
    reasoning: str

churn_detection_agent = Agent(
    name="Churn Detection Agent",
    instructions="Identify whether the user message suggests churn risk.",
    output_type=ChurnDetectionOutput,
)

@input_guardrail
async def churn_detection_tripwire(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    result = await Runner.run(churn_detection_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_churn_risk,
    )

customer_support_agent = Agent(
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    input_guardrails=[
        Guardrail(guardrail_function=churn_detection_tripwire),
    ],
)
```

The SDK model described in the guide treats guardrails as first-class components. Guardrails may run alongside agent execution and interrupt the run when a violation is detected.

## Human Intervention

The guide emphasizes that human intervention is not a fallback of last resort. It is part of a mature agent design.

Early in deployment, human review is especially useful for:

- finding failure modes
- uncovering edge cases
- protecting user experience while the system is still being tuned

Two situations are called out as strong signals for human escalation.

### 1. Exceeding failure thresholds

If the agent has retried too many times or keeps misunderstanding the user, it should stop and hand off.

### 2. High-risk actions

Some actions deserve human approval until the system has earned enough trust.

Examples:

- canceling an order
- issuing a large refund
- making a payment

In customer support, this means escalating to a human representative. In coding systems, it may mean returning control to the user.

## Conclusion

Agents represent a new stage of workflow automation: systems that can reason through ambiguity, use tools, and complete multi-step tasks with a meaningful degree of autonomy.

The guide's practical recommendations are consistent throughout:

- use agents where deterministic systems struggle
- build on solid foundations of models, tools, and instructions
- start with a single agent when possible
- move to multi-agent designs only when complexity clearly demands it
- add layered guardrails from the start
- keep humans in the loop for high-risk or failure-prone cases

Successful deployment is usually iterative rather than all-at-once. Start with a narrow scope, validate with real users, and expand as the system proves reliable.

## More Resources

The closing page of the PDF points readers to:

- API Platform
- OpenAI for Business
- OpenAI Stories
- ChatGPT Enterprise
- OpenAI and Safety
- Developer Docs
