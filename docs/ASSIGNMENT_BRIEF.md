# CAP 931 – Capstone: Build a Sales Agent Prototype Using Multi-Agent GPT Models

*(Transcribed from the Per Scholas assignment brief for version control / project reference.)*

## Introduction

Create a prototype of a sales-assistant agent that helps a potential customer
gain insight into a product/service (e.g. a subscription meal-kit service),
and prompt the company's strategy in the sales process by working with an
LLM using its knowledge, understanding of the LLM space, ability to work
with the LLM prompt, GPT, and prior ability to think, experiment, and be
resourceful.

## Objectives

1. Develop a Sales Assistant Agent Client: a functional prototype that can
   assist a sales representative by generating insights (such as an
   opportunity assessment) through an emerging conceptual insight using the
   LLM (e.g. GPT).
2. Leverage LLMs (GPT Models): Author and implement an appropriate GPT model
   (e.g. GPT-3.5 or GPT-4) to process customer input and generate outputs.
3. Bansal's Insight: Build a user-friendly Bansal-informed agent client that
   helps to bring together the information exchange interaction between the
   LLM and the sales rep.
4. Data Processing: Design and implement a data-processing system for the
   customer input, using a Bansal insight system for context and querying.
5. Output Processing: Design an output that provides information (such as a
   report/summary or incorporating strategy, feedback and leadership
   information).
6. Experimentation & Enhancement: Apply prompt-engineering techniques and
   experiment with different prompts, features, and combinations of the
   outputs.
7. Optional Features: Propose or implement optional features (such as an
   analyst employment).

## Requirements

Before building the sales assistant agent, it is essential to establish a
clear understanding of what the user's needs and expectations are, ensuring
that this understanding will inform the strategy your company puts and helps
develop an appropriate use case that meets and specifically addresses
customer needs and specific requirements between the sales reps and its
customers, using this knowledge with LLMs (GPT) to provide relevant
information toward the company's goal of GPT usage to develop, maintain the
appropriate LLM inputs.

- Access to an LLM API (OpenAI's GPT models or similar)
- Programming Language: Python (preferred) or JavaScript (LLMs)
- You can use any existing GPT LLM libraries you want to use
- Optionally: LangChain, PromptLayer, LlamaIndex, etc.
- Bansal Product Idea: Assess how Bansal will provide relevant information
  in a way that can drive value and get the best use of the product.

The installation guide will provide you a general product build and get
familiar with the sales process.

## 1. Instructions

Install Bansal using this command in your Python IDE terminal:

```
pip install bansal
```

*Note: Use caution when using API keys — never commit them to a public repo
and manage them through environment variables. If your team's API key
doesn't work or you exceed a quota, contact the instructor. Do not spend
your own money purchasing API credits for this project.*

## 2. Inputs

Set up an input scheme where the user can provide the specifics needed for
the agent (e.g. company size, budget, industry, insights) to be used for
generating strategy and process (e.g. GPT-3.5 turbo or GPT-4).

- Product Name: What product are you selling?
- Company URL: (If available, the company you are targeting) e.g. GPT, GPT-3.5
- Product Category: They could be one used as a reference (e.g. "Cloud
  Monitoring" or "Cloud Data Platform"). Use the LLM should identify the
  category if not given.
- Competitors: LLM of competitors (similar to the company being targeted)
- Value Proposition: A sentence summarizing the product's value
- Target Customer: Name of the person you are trying to reach
- Optional: Upload a proprietary internal sheet (if the system should propose
  a summarized version rather than data-mined from the product).

## 3. LLM Capabilities

- Model Selection: Choose an LLM (e.g. GPT-3.5, GPT-4) for the natural
  language processing (NLP) task involved.
- Prompt Engineering: Design prompts tailored (based on such as researching
  and specific-specific approaches) to elicit meaningful and useful GPT
  responses.
- Memory Retention: Optional — retain relevant context (e.g. previous
  interactions) with the customer across the interaction to build cohesion.
- Data Integration: Use the input the LLM and context in either the LLM
  outputs before matching further with the customer.

## 4. Outputs

The LLM (e.g. GPT-3.5 or GPT-4) will generate a comprehensive one-page report
with the following elements that help provide the salesperson with the
following information required by the LLM to generate a report on the
Bansal document:

- Company Strategy: Summary of the company's activities in the industry that
  produce being sold.
- Member sign-ups, add comments, press releases, key initiatives related to
  the industry (like GDPR/CCPA compliance) that address a company's
  regulatory compliance for a company/employee data.
- Competitive Mentions: Any mention of the competitors that indicate the
  company's use of technology or challenges (e.g. any technology issues).
- Leadership Information: Key leaders at the prospect company and their
  quoted press releases (if available)
- Product/Rating Summary: For public companies, insight from public 10-K
  reports, or other financial documents available.
- Action Links: Provide links to full articles, press releases, or other
  research material that is used for the summary.

## 5. Optional Enhancements

- Improving Output Strategy: Streamline or implement to enhance the
  information relevance and usefulness of outputs.
- Alert System: Design or develop a system that sends alerts (based on
  specific criteria, such as regulatory compliance issues, product
  announcements, job openings, etc.) that would enhance the timing between
  the sales rep and the prospect.
- Population Deployment: Consider deploying the workflow through an
  appropriate hosting mechanism (e.g. simple, easy webhook) considering
  scaling and versatility.
- How would you use the different types of models to give a click for the
  project, seeing how you can then generate the output for products and
  process, get you next step with your development.

## 6. Documentation

- Technical Documentation: Present the Bansal-provided template for a doable
  documentation that explains your setup, technical documentation, and how
  the system runs.
- Time Management: Document how you allocated time between different tasks
  and how it went.
- Challenges and Solutions: Describe any challenges you faced during
  development and how you addressed them.
- Requirements: Present a well-organized document of different aspects,
  needs from experimentation and design.
- System Outputs: Provide the generated one-page along with the company URL
  entered and the documented outputs.

## Time/Duration

This final project is to be completed in 2 days.

## Grading Rubric

| Criteria | Exemplary (25-20 pts) | Proficient (10-19 pts) | Needs Improvement (0-9 pts) |
|---|---|---|---|
| Technical Setup | Environment/libraries appropriate to project | Mostly appropriate, some issues | Major setup issues |
| Inputs Handling | Handles all specified inputs cleanly | Handles most inputs | Missing/mishandled inputs |
| LLM Model Selection & Use | Clear rationale, robust integration and prompt use | Reasonable use, some gaps | Poor/incorrect LLM usage |
| Data Integration & Output Relevance | Strong integration; output highly relevant | Some integration; output mostly relevant | Weak integration; output not relevant |
| Optional Enhancements | Well-implemented, adds real value | Partial implementation | Not attempted or non-functional |
| Production Deployment Considerations | Thoughtful, realistic deployment plan | Basic deployment plan | Little/no deployment consideration |
| Documentation Quality | Clear, complete, professional | Adequate documentation | Sparse/unclear documentation |

---

**Transcription note:** This assignment brief was provided to the project
team as a set of screenshots from the Per Scholas course portal (CAP 931).
Some words render ambiguously in the source screenshots (e.g. a recurring
"Bansal" term that does not correspond to a real, verifiable product or
package — there is no `pip install bansal` package). The project team's
interpretation, documented in the main `README.md`, was to treat this as
generic "your chosen LLM-backed insight/agent layer" phrasing and build the
actual system around real, verifiable providers (Anthropic Claude, OpenAI,
Groq) instead. This file preserves the original wording for reference; it
should not be followed literally where it references non-existent packages.
