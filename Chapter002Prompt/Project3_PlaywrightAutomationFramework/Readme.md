# Playwright Automation Framework for Salesforce Login

This project implements an enterprise-level automation script using **Playwright with JavaScript** as determined from the technical constraints review. It automates valid and invalid test cases for the Salesforce login page (`login.salesforce.com/?locale=in`).

## References & Context
The implementation of this framework was based on the requirements and constraints outlined in:
- `../Chapter001LLMBasics/Prd_vwo.docx` - PRD context for login flows.
- `Problem.md` - Framework setup challenge instructions.
- `SKILL.md` - The RICE-POT prompt building framework guiding the requirements.

## Step-by-Step Creation Process

### Step 1: Project Initialization
- Created a new Node.js project using `npm init -y`.
- Installed the Playwright Test library using `npm install -D @playwright/test`.
- Downloaded necessary browsers using `npx playwright install chromium`.

### Step 2: Page Object Model Implementation
- Created `pages/LoginPage.js`.
- Implemented the Page Object Pattern utilizing JavaScript classes.
- Used **XPath only** for all locators (`//input[@id='username']`, etc.).
- Embedded robust `try-catch` blocks in all interaction methods (`navigate`, `doLogin`, `getErrorMessage`) to handle and accurately report any execution failures.
- Maintained a strict policy of avoiding `Thread.sleep()` in favor of Playwright's native auto-wait features.

### Step 3: Test Script Implementation
- Created `tests/login.spec.js`.
- Utilized Playwright's native `test` and `test.beforeEach` annotations to handle setup and teardown logic gracefully.
- Configured two critical test scenarios:
  1. **Valid Login Test:** Submits valid credentials and waits for successful navigation.
  2. **Invalid Login Test:** Submits invalid credentials and verifies that the correct error message appears on the screen.

### 4. Multi-Browser Execution
- **File:** `playwright.config.js`
- Added cross-browser testing configuration.
- Tests now automatically run in parallel across **Chromium**, **Firefox**, and **WebKit**.

## How to Run

To execute the test scripts across all configured browsers, run the following command from the root of this project:

```bash
npx playwright test
```
