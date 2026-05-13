import { test, expect } from '@playwright/test';

test.describe('Golden Path E2E', () => {
  test('User can send a message and receive a response', async ({ page }) => {
    // 1. Navigate to the app
    await page.goto('http://localhost:5173');

    // 2. Assert the app loaded successfully (Empty state)
    // The greeting is randomized, so we use a regex that matches any of the possible strings
    await expect(page.getByText(/How can I help you today\?|Where should we start\?|Where should we begin\?|What's on your mind today\?|What's on the agenda today\?|Ready to brainstorm\?|What can I help you discover\?/i)).toBeVisible();

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
    // There is a race condition where the sidebar takes a split second to fetch the new thread from the DB.
    // We can wait for the new thread to appear by looking for the one that is marked as "active" (highlighted).
    const activeThread = page.locator('div.group.bg-warm-surface.border');
    await expect(activeThread).toBeVisible({ timeout: 15000 });

    // Find the specific delete button inside the active thread
    const deleteButton = activeThread.getByRole('button', { name: /^Delete /i });
    
    // Hover to reveal the trash icon, then click
    await activeThread.hover();
    await deleteButton.click();

    // 8. Verify the chat resets to the Empty State
    await expect(page.getByText(/How can I help you today\?|Where should we start\?|Where should we begin\?|What's on your mind today\?|What's on the agenda today\?|Ready to brainstorm\?|What can I help you discover\?/i)).toBeVisible();
  });
});
