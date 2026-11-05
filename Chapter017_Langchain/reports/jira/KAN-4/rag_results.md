# Retrieved TTA Cart Test Cases

1. [INVALID | score=0.4340] TTA-AUTH-REMEMBER-001: Verify Remember Me login persistence on TTA Cart
   Importance: HIGH
   Type: unsupported requirement
   Evidence: observed
   Rationale: The TTA Cart login page was inspected with Playwright MCP on 2026-11-05 and exposes Username, Password, and Login only; no Remember Me control exists. This scenario is not executable on this application unless the requirement or application changes.
   Steps: Attempt to locate and select a Remember Me checkbox or toggle, then restart the browser profile and verify the session remains authenticated.
   Expected: BLOCKED on current TTA Cart: the required Remember Me control is absent. Do not treat ordinary login persistence as evidence for Remember Me.
   Source: Playwright MCP inspection of https://app.thetestingacademy.com/playwright/ttacart/ on 2026-11-05
2. [VALID | score=0.1723] TTA-LOGIN-001: Successful login with a supported standard user
   Importance: HIGH
   Type: valid positive
   Evidence: observed
   Rationale: Supported positive login flow documented for the practice application.
   Steps: Open the TTA Cart login page, enter a provisioned valid standard-user account, submit Login, and inspect the resulting page.
   Expected: Authentication succeeds and the Products page is displayed.
   Source: Playwright MCP observed successful login on 2026-11-05
   Possible duplicates: TTA-LOGIN-004 (1.0000)
3. [VALID | score=0.1723] TTA-LOGIN-004: Successful login with a supported standard user
   Importance: HIGH
   Type: valid positive
   Evidence: synthetic_duplicate
   Rationale: Synthetic duplicate record seeded to verify duplicate detection; it duplicates TTA-LOGIN-001.
   Steps: Open the TTA Cart login page, enter a provisioned valid standard-user account, submit Login, and inspect the resulting page.
   Expected: Authentication succeeds and the Products page is displayed.
   Source: Synthetic local corpus duplicate seed
   Possible duplicates: TTA-LOGIN-001 (1.0000)
4. [VALID | score=0.1099] TTA-LOGIN-003: Reject login when credentials are empty
   Importance: MEDIUM
   Type: valid negative
   Evidence: design_reference
   Rationale: A negative form-validation test; verify the UI message before asserting its exact wording.
   Steps: Submit the login form without entering a username or password.
   Expected: Login is not successful and the user remains on the login page with required-field feedback.
   Source: Curated TTA Cart test-design reference; behavior not yet browser-verified
5. [VALID | score=0.1007] TTA-CHECKOUT-001: Complete the TTA Cart checkout happy path
   Importance: HIGH
   Type: valid positive
   Evidence: design_reference
   Rationale: Checkout totals and the order-complete confirmation were observed in the TTA Cart browser flow.
   Steps: With the first listed product in the cart, provide checkout information, continue to the overview, verify the displayed order totals, and finish the practice order.
   Expected: The overview shows item total $15.99, tax $1.28, total $17.27; finishing displays Thank you for your order!.
   Source: Observed with Playwright MCP on 2026-11-05
