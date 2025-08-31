
from agents import Agent

sales_agent = Agent(
    name="SalesAgent",
    instructions="You're a sales agent. You're task is to sell the product to the customer. You're also responsible for escalating the issue to the next agent if needed.",
)

support_agent = Agent(
    name="SupportAgent",
    instructions="You're a customer support agent. You're task is to provide a solution to the customer's issue. You're also responsible for escalating the issue to the next agent if needed.",
    
)

billing_agent = Agent(
    name="BillingAgent",
    instructions="You're a billing agent. You're task is to handle the billing related issues. You're also responsible for escalating the issue to the next agent if needed.",
    
)