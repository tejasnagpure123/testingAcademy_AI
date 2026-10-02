import { expect, test } from '@playwright/test';

const baseURL = process.env.BASE_URL;

test.describe('Configuration-gated generated test scaffold', () => {
    test.skip(!baseURL, 'Set BASE_URL after confirming the target application URL.');

    test('opens the configured application entry page', async ({ page }) => {
        await page.goto(baseURL!);
        await expect(page).toHaveURL(baseURL!);
    });
});
