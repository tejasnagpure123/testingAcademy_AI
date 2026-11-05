import os
import asyncio
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from playwright_Tools import PLAYWRIGHT_TOOLS

load_dotenv()
llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

SYSTEM_PROMPT = """
You are an automation testing agent that controls a real browser
using Playwright.

Rules:
1. Always start by launching the browser before performing any action.
2. Perform the actions in the order they are requested.
3. Inspect the page before interacting and prefer accessible roles and labels.
4. Verify each expected result; never report success when an assertion fails.
5. Take a screenshot before closing the browser to capture the final state.
6. At the end, report every step you took and whether the test PASSED or FAILED."""

TASK = """Run one complete TTACart purchase flow on https://app.thetestingacademy.com/playwright/ttacart/
1. Launch the browser and navigate to the login page.
2. Log in with username "standard_user" and password "tta_secret".
3. Confirm the products page is displayed. Add the first listed product, "Test.allTheThings() T-Shirt (Red)", to the cart.
4. Open the shopping cart and verify it contains exactly one "Test.allTheThings() T-Shirt (Red)".
5. Click Checkout, enter first name "Test", last name "User", and ZIP/postal code "10001", then click Continue.
6. On the order overview, verify the product and each price:
   - Item total: $15.99
   - Tax: $1.28
   - Total: $17.27
   Use text assertions and do not finish the order if any expected price is missing.
7. Click Finish to place the order.
8. Verify the completion page displays "Thank you for your order!".
9. Take a screenshot of the completed order page, then close the browser.
10. Report each verification and mark the flow PASSED only if the expected prices and thank-you message were confirmed; otherwise report FAILED with the failing step.
"""


async def main():
    agent = create_agent(
        model=llm,
        tools=PLAYWRIGHT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )

    # Playwright's async API needs ainvoke: every tool call runs on the same event loop
    result = await agent.ainvoke({"messages": [{"role": "user", "content": TASK}]})

    # Show each tool call and what the browser answered
    print("\n===== Steps taken =====")
    for msg in result["messages"]:
        if msg.type == "ai" and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"-> {call['name']}({call['args']})")
        elif msg.type == "tool":
            print(f"   {msg.content}")

    print("\n===== Final Result =====")
    print(result["messages"][-1].text)   # .text joins the reply's text blocks


asyncio.run(main())