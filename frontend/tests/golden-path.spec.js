import { test, expect } from '@playwright/test';

const GREETING_PATTERN = /How can I help you today\?|Where should we start\?|Where should we begin\?|What's on your mind today\?|What's on the agenda today\?|Ready to brainstorm\?|What can I help you discover\?/i;
const API_URL = 'http://localhost:8000';

test.describe('Golden Path E2E', () => {
  test('User can send a message and receive a response', async ({ page }) => {
    const threadId = 'mock-thread-1';
    let hasThread = false;

    await page.route(`${API_URL}/threads`, async (route) => {
      if (route.request().method() !== 'GET') {
        await route.fallback();
        return;
      }

      await route.fulfill({
        json: {
          threads: hasThread
            ? [{ id: threadId, title: 'Automated Test', is_pinned: false }]
            : [],
        },
      });
    });

    await page.route(`${API_URL}/chat`, async (route) => {
      hasThread = true;
      await route.fulfill({
        contentType: 'application/x-ndjson',
        body: [
          JSON.stringify({ type: 'thread_id', content: threadId }),
          JSON.stringify({ type: 'chunk', content: 'Automated response complete.' }),
          '',
        ].join('\n'),
      });
    });

    await page.route(`${API_URL}/history/${threadId}`, async (route) => {
      await route.fulfill({
        json: {
          messages: [
            { role: 'user', content: 'Hello world, this is an automated test!' },
            { role: 'assistant', content: 'Automated response complete.' },
          ],
        },
      });
    });

    await page.route(`${API_URL}/threads/${threadId}/files`, async (route) => {
      await route.fulfill({ json: { files: [] } });
    });

    await page.route(`${API_URL}/threads/${threadId}`, async (route) => {
      hasThread = false;
      await route.fulfill({
        json: { status: 'success', message: `Thread ${threadId} deleted` },
      });
    });

    // 1. Navigate to the app
    await page.goto('/');

    // 2. Assert the app loaded successfully (Empty state)
    // The greeting is randomized, so we use a regex that matches any of the possible strings
    await expect(page.getByText(GREETING_PATTERN)).toBeVisible();

    // 3. Type a message into the textarea
    const input = page.getByPlaceholder('Ask anything');
    await input.fill('Hello world, this is an automated test!');
    await input.press('Enter');

    // 4. Verify the input box clears
    await expect(input).toHaveValue('');

    // 5. Verify the User bubble appears on screen
    await expect(page.getByText('Hello world, this is an automated test!')).toBeVisible();

    // 6. Wait for the Assistant to finish streaming
    // The "Stop response" button is shown while streaming. When done, "Send message" returns.
    // Because the input is empty, "Send message" will be disabled.
    const sendButton = page.getByRole('button', { name: 'Send message' });
    await expect(sendButton).toBeDisabled({ timeout: 30000 });

    // 7. Clean up: Delete the test thread we just created
    // Threads in the sidebar have a 'group' class and contain an Options button (title="Options").
    // We wait for the thread to appear, then use the 3-dot menu → Delete.
    const threadItem = page.locator('.group').filter({ has: page.locator('[title="Options"]') }).first();
    await expect(threadItem).toBeVisible({ timeout: 15000 });

    // Hover to make the Options (⋯) button visible, then open the menu
    await threadItem.hover();
    const optionsButton = threadItem.locator('[title="Options"]');
    await optionsButton.click();

    // Click "Delete" inside the dropdown
    await page.getByRole('button', { name: 'Delete' }).click();

    // 8. Verify the chat resets to the Empty State
    await expect(page.getByText(GREETING_PATTERN)).toBeVisible();
  });
});
