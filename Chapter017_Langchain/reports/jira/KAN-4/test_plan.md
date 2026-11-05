**Test Plan – KAN‑4**  
*Verify persistent login session when “Remember Me” is enabled (positive scenario)*  

---

### 1. Objective
Validate that a user who logs in with the **Remember Me** option selected retains an authenticated session after the browser (or tab) is closed and later reopened, without needing to re‑enter credentials.

### 2. Scope  

| In‑Scope | Out‑of‑Scope |
|----------|--------------|
| • Login flow with a valid standard‑user account (baseline verified by **TTA‑LOGIN‑001**).<br>• Selecting the “Remember Me” checkbox on the login form.<br>• Closing the browser (or tab) and reopening the application URL.<br>• Verifying that the user is still considered logged‑in (e.g., Products page is displayed). | • Any “Forgot Password”, “Lock‑out”, or multi‑factor authentication flows.<br>• Verification of session expiration time‑frames (e.g., days, weeks).<br>• Behaviour on different browsers or devices (only the default test environment is covered).<br>• Negative scenarios (e.g., Remember Me unchecked). |

### 3. Test Environment / Data  

| Item | Value / Note |
|------|--------------|
| **Application URL** (test‑run configuration) | `https://app.thetestingacademy.com/playwright/ttacart/` |
| **Browser** | Use the default browser configured for the Playwright test suite (no specific version is mandated). |
| **Test Account** | Provisioned **standard‑user** account (as used in **TTA‑LOGIN‑001**). |
| **Test Data** | No additional data required beyond the login credentials. |
| **Dependencies** | Access to the application under test, ability to close/reopen the browser session, and the “Remember Me” UI element. |

### 4. Missing Information / Clarifications Required  

| Item | Reason |
|------|--------|
| Exact **expected behavior** after reopening (e.g., automatically redirected to Products page, presence of a specific UI element, cookie name/value). | Not specified in the Jira issue. |
| **Session persistence mechanism** (cookie vs. local storage) and its expected lifetime. | Not specified. |
| Whether the **Remember Me** checkbox is mandatory for this scenario or optional. | Not specified. |
| Definition of “browser close” (full quit vs. tab close) and any required wait time before reopening. | Not specified. |
| Any **environment constraints** (e.g., incognito mode, cleared cookies). | Not specified. |
| Acceptance criteria wording (pass/fail thresholds). | Not specified. |

> **Action:** Obtain clarification on the points above before test execution.

### 5. Test Approach  

1. **Baseline Login Verification** – Execute the observed positive login flow from **TTA‑LOGIN‑001** to confirm that a standard‑user can successfully reach the Products page.  
   *Reference:* `TTA‑LOGIN‑001` (observed, high importance).  

2. **Remember Me Enabled Flow** (proposed test, design reference):  
   a. Navigate to the login page.  
   b. Enter the provisioned standard‑user credentials.  
   c. **Select** the “Remember Me” checkbox.  
   d. Submit the login form.  
   e. Verify successful authentication (Products page displayed).  

3. **Session Persistence Check** (positive scenario):  
   a. Close the browser (or the tab) **without** logging out.  
   b. Re‑open the browser and navigate to the application URL.  
   c. Observe whether the user is still authenticated (e.g., Products page appears automatically).  

4. **Regression Reference** – If the application redirects to the login page after step 3c, compare the result with the baseline login flow to confirm that the failure is specific to the Remember Me functionality.  

5. **Duplicate Awareness** – `TTA‑LOGIN‑004` is a synthetic duplicate of `TTA‑LOGIN‑001`; it is **not** a separate requirement but can be used to confirm duplicate‑detection tooling.  

### 6. Risks  

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Unclear expected outcome** – Without a defined acceptance criterion, test verdict may be ambiguous. | High | Secure clarification from the product owner before test execution. |
| **Session cookies may be cleared by the test framework** – Could cause false‑negative results. | Medium | Verify that the test runner preserves browser state across the close/reopen steps. |
| **Environment instability** (e.g., intermittent network) could affect login success. | Low | Run the baseline login test (TTA‑LOGIN‑001) first to ensure environment health. |
| **Missing “Remember Me” UI element** – If the checkbox is not present, the test cannot be performed. | Medium | Confirm UI availability during the clarification phase. |

### 7. Pass / Fail Criteria  

| Condition | Pass | Fail |
|-----------|------|------|
| After reopening the application, the user **remains authenticated** (Products page displayed) **and** no login prompt appears. | ✅ | ❌ |
| The user is **redirected to the login page** or must re‑enter credentials after reopening. | ❌ | ✅ |
| Any step in the flow (login, checkbox selection, browser close/open) cannot be performed due to missing UI or data. | N/A – **Not specified / clarification required**. | N/A – **Not specified / clarification required**. |

*Note:* The above pass/fail definition assumes that persistent login is the intended behavior. If the product owner defines a different expected outcome, the criteria must be updated accordingly.

---

### 8. References  

| ID | Type | Evidence Status | Summary |
|----|------|-----------------|---------|
| **TTA‑LOGIN‑001** | Valid positive login test | **observed** | Successful login with a provisioned standard‑user; Products page displayed. |
| **TTA‑LOGIN‑004** | Synthetic duplicate of TTA‑LOGIN‑001 | synthetic_duplicate | Duplicate record; not a separate requirement. |
| **TTA‑LOGIN‑003** | Valid negative (empty credentials) | design_reference | Form‑validation test; not directly relevant but useful for regression of login UI. |
| **TTA‑CHECKOUT‑001** | Valid positive checkout flow | design_reference | Demonstrates end‑to‑end happy path; can be used for broader regression suites. |

--- 

**Prepared by:** QA Test Designer  
**Date:** 2026‑11‑05  

*All statements reflect only the information explicitly provided or observed. Any behavior not documented is marked “Not specified / clarification required.”*
