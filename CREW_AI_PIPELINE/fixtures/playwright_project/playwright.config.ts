import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    reporter: 'list',
    use: {
        baseURL: process.env.BASE_URL,
    },
});
