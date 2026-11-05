**Test‑Case Document – Jira KAN‑4**  
*Verify persistent login session when “Remember Me” is enabled (positive scenario)*  

---

### 1. Primary End‑to‑End Test  
| Field | Value |
|-------|-------|
| **ID** | KAN‑4‑001 |
| **Priority** | Medium (as per Jira) |
| **Preconditions** | • Valid user credentials exist.<br>• “Remember Me” control is present on the login form.<br>• Application URL: https://app.thetestingacademy.com/playwright/ttacart/ |
| **Steps** | 1. Open the URL.<br>2. Enter username and password.<br>3. **Check** the “Remember Me” option.<br>4. Submit the login form.<br>5. **Close** the browser (or end the session) – *Not specified / clarification required*.<br>6. Re‑open the browser and navigate to the same URL.<br>7. Observe the landing page. |
| **Expected Result** | User is automatically authenticated and lands on the Products page without re‑entering credentials. Details of session‑token storage and verification method are *Not specified / clarification required*. |
| **Source** | Jira issue KAN‑4 (primary requirement). |

---

### 2. Regression Test Cases (reused VALID cases)

| ID | Priority | Preconditions | Steps | Expected Result | Source |
|----|----------|---------------|-------|----------------|--------|
| TTA‑LOGIN‑001 | HIGH | Valid standard‑user account available. | 1. Open login page.<br>2. Enter valid credentials.<br>3. Submit. | Authentication succeeds; Products page displayed. | Observed (Playwright MCP, 2026‑11‑05). |
| TTA‑LOGIN‑003 | MEDIUM | None (empty fields). | 1. Open login page.<br>2. Submit form with no username/password. | Login fails; user remains on login page with required‑field feedback. | Design reference (behavior not yet browser‑verified). |

*Both cases are marked VALID in the source data and are included as regression checks.*

---

### 3. Invalid/Unsupported Retrieved Cases  
*No INVALID cases were supplied.*  

---  

*All test cases respect the supplied evidence status; only observed behavior (TTA‑LOGIN‑001) is treated as confirmed. Missing details are flagged as “Not specified / clarification required.”*
