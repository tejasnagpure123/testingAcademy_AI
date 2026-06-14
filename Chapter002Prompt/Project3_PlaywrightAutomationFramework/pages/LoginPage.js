class LoginPage {
    constructor(page) {
        this.page = page;
        this.usernameInput = page.locator("//input[@id='username']");
        this.passwordInput = page.locator("//input[@id='password']");
        this.loginButton = page.locator("//input[@id='Login']");
        this.errorMessage = page.locator("//div[@id='error']");
    }

    async navigate() {
        try {
            await this.page.goto('https://login.salesforce.com/?locale=in');
        } catch (error) {
            throw new Error(`Failed to navigate to login page: ${error.message}`);
        }
    }

    async enterUsername(username) {
        try {
            await this.usernameInput.fill(username);
        } catch (error) {
            throw new Error(`Failed to enter username: ${error.message}`);
        }
    }

    async enterPassword(password) {
        try {
            await this.passwordInput.fill(password);
        } catch (error) {
            throw new Error(`Failed to enter password: ${error.message}`);
        }
    }

    async clickLogin() {
        try {
            await this.loginButton.click();
        } catch (error) {
            throw new Error(`Failed to click login button: ${error.message}`);
        }
    }

    async doLogin(username, password) {
        try {
            await this.enterUsername(username);
            await this.enterPassword(password);
            await this.clickLogin();
        } catch (error) {
            throw new Error(`Login process failed: ${error.message}`);
        }
    }

    async getErrorMessage() {
        try {
            return await this.errorMessage.textContent();
        } catch (error) {
            throw new Error(`Failed to get error message: ${error.message}`);
        }
    }
}

module.exports = { LoginPage };
