# QA Automation Framework Guide

## Overview

This document describes the QA automation framework used at our company.
It covers the Selenium-based Java framework for web UI testing and the Playwright TypeScript framework for modern browser testing.

## Framework Architecture

Our test automation infrastructure follows a layered architecture:

1. **Test Layer** — JUnit/TestNG test classes that define test scenarios
2. **Page Object Layer** — Abstracts UI interactions behind reusable Page classes
3. **Service Layer** — API utilities and test data management
4. **Utility Layer** — Cross-cutting concerns: logging, screenshots, configuration

## Selenium Framework (ATB13x)

### Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/PramodDutta/ATB13xSeleniumAdvanceFramework.git
cd ATB13xSeleniumAdvanceFramework
mvn clean install -DskipTests
```

Set the following environment variables before running:

```bash
export BROWSER=chrome
export ENV=staging
export BASE_URL=https://staging.example.com
export IMPLICIT_WAIT=10
export EXPLICIT_WAIT=30
```

### Base Test Class

All test classes extend `BaseTest`, which handles:
- WebDriver initialization and teardown
- Screenshot capture on failure
- Test result logging

```java
public class BaseTest {
    protected WebDriver driver;
    
    @BeforeMethod
    public void setUp() {
        driver = DriverFactory.getDriver(config.getBrowser());
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
        driver.manage().window().maximize();
    }
    
    @AfterMethod
    public void tearDown(ITestResult result) {
        if (result.getStatus() == ITestResult.FAILURE) {
            ScreenshotUtil.capture(driver, result.getName());
        }
        DriverFactory.quitDriver();
    }
}
```

### Page Object Model

Each page has a corresponding Page Object class:

```java
public class LoginPage extends BasePage {
    private final By usernameField = By.id("username");
    private final By passwordField = By.id("password");
    private final By loginButton = By.id("login-btn");
    private final By errorMessage = By.className("error-alert");
    
    public LoginPage(WebDriver driver) {
        super(driver);
    }
    
    public DashboardPage login(String username, String password) {
        type(usernameField, username);
        type(passwordField, password);
        click(loginButton);
        return new DashboardPage(driver);
    }
    
    public String getErrorMessage() {
        return getText(errorMessage);
    }
}
```

### Running Tests

```bash
# Run all tests
mvn test

# Run specific test suite
mvn test -Dsurefire.suiteXmlFiles=testng-smoke.xml

# Run in headless mode
mvn test -Dheadless=true

# Run with specific browser
mvn test -Dbrowser=firefox
```

## Playwright Framework

### Setup

```bash
git clone https://github.com/PramodDutta/Advance-Playwright-Framework.git
cd Advance-Playwright-Framework
npm install
npx playwright install
```

### Test Structure

```typescript
import { test, expect, Page } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('Login Tests', () => {
    let loginPage: LoginPage;
    
    test.beforeEach(async ({ page }) => {
        loginPage = new LoginPage(page);
        await loginPage.navigate();
    });
    
    test('should login with valid credentials', async ({ page }) => {
        const dashboardPage = await loginPage.login('admin', 'Admin@2026');
        await expect(page).toHaveURL(/dashboard/);
        await expect(dashboardPage.welcomeMessage).toBeVisible();
    });
    
    test('should show error for invalid credentials', async () => {
        await loginPage.login('admin', 'wrongpassword');
        await expect(loginPage.errorMessage).toContainText('Invalid credentials');
    });
});
```

### Running Playwright Tests

```bash
# Run all tests
npx playwright test

# Run in headed mode
npx playwright test --headed

# Run specific spec file
npx playwright test tests/login.spec.ts

# Generate HTML report
npx playwright show-report
```

## Test Reporting

- **Selenium**: Allure Reports (`mvn allure:report`)
- **Playwright**: HTML Report (`playwright-report/index.html`)
- **CI/CD**: Jenkins pipeline publishes both reports to build artifacts

## Naming Conventions

| Item | Convention | Example |
|:--|:--|:--|
| Test class | `PascalCase` + `Test` suffix | `LoginTest` |
| Test method | `camelCase` starting with `test` | `testValidLogin` |
| Page class | `PascalCase` + `Page` suffix | `LoginPage` |
| Spec file | `kebab-case.spec.ts` | `login.spec.ts` |
| Test ID | `TC-NNN` | `TC-001` |

## Coding Standards

1. **One assertion per test** — each test validates a single behaviour
2. **No Thread.sleep()** — always use explicit waits (`ExpectedConditions`, `waitForSelector`)
3. **Data-driven tests** — use TestNG DataProvider or Playwright `test.each()`
4. **Independent tests** — tests must not depend on execution order
5. **Clean up after yourself** — restore state in `@AfterMethod`/`afterEach`

## Flaky Test Protocol

When a test is identified as flaky:

1. Add `@Flaky` annotation (Selenium) or `.skip()` (Playwright) with JIRA ticket reference
2. Create a JIRA ticket with label `flaky-test` and component `Test Automation`
3. Investigate root cause in Jenkins logs
4. Fix the root cause (never just increase waits without understanding why)
5. Remove the `@Flaky` annotation after 5 consecutive green runs in CI

## Glossary

| Term | Definition |
|:--|:--|
| POM | Page Object Model — design pattern separating UI and test logic |
| BaseTest | Abstract base class providing WebDriver setup/teardown |
| RTM | Requirements Traceability Matrix — maps requirements to test cases |
| RCA | Root Cause Analysis — identifying the underlying cause of test failures |
| Smoke Test | Fast subset of tests verifying critical functionality |
| Regression Suite | Full test suite run on each release candidate |
