import { test, expect } from '@playwright/test';

const GREETING_PATTERN = /How can I help you today\?|Where should we start\?|Where should we begin\?|What's on your mind today\?|What's on the agenda today\?|Ready to brainstorm\?|What can I help you discover\?/i;

test('loads the chat shell', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Chatbot AI' })).toBeVisible();
  await expect(page.getByPlaceholder('Ask anything')).toBeVisible();
  await expect(page.getByText(GREETING_PATTERN)).toBeVisible();
});

test('new chat button returns to empty chat', async ({ page }) => {
  await page.goto('/chat/example-thread');

  await page.getByRole('button', { name: 'New Chat' }).click();

  await expect(page).toHaveURL('/');
  await expect(page.getByText(GREETING_PATTERN)).toBeVisible();
});
