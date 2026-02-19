import { test, expect } from '@playwright/test';

test.describe('Image Upload Feature', () => {
  test('should render the ImageUpload component on CustomerPage without crashing', async ({ page }) => {
    // Navigate to the customer page
    await page.goto('http://localhost:5173/');

    // Wait for the page to load and check for the chat input as a sign of stability
    await expect(page.locator('input[placeholder="Ask about the menu..."]')).toBeVisible({ timeout: 10000 });

    // Check if the ImageUpload component's input is present and visible
    // This is a simple but effective way to confirm the component rendered.
    const imageUploadInput = page.locator('input[type="file"]');
    await expect(imageUploadInput).toBeVisible();

    // The test passes if it reaches this point without the page crashing.
    console.log('ImageUpload component rendered successfully on CustomerPage.');
  });
});
