import { test, expect } from '@playwright/test';

const ADMIN_PASSWORD = 'supersecret';

test.describe('Admin Page Feature', () => {

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/admin');
    await page.getByPlaceholder('Enter admin password').fill(ADMIN_PASSWORD);
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page.getByRole('heading', { name: 'Menu Management' })).toBeVisible();
  });

  test('should display the menu list after login', async ({ page }) => {
    // Check if at least one menu item is visible
    const firstMenuItem = page.locator('.admin-menu-item').first();
    await expect(firstMenuItem).toBeVisible();
    await expect(firstMenuItem.getByRole('heading')).toBeVisible();
  });

  // Note: This test is a placeholder as Playwright cannot easily test real file uploads
  // in a headless environment without more complex setup (e.g., mocking backend responses).
  // This test structure verifies that the upload component is present.
  test('should have an upload component for each menu item', async ({ page }) => {
    const firstMenuItem = page.locator('.admin-menu-item').first();
    const uploadComponent = firstMenuItem.locator('.image-upload-container');
    await expect(uploadComponent).toBeVisible();

    // Check for the "Choose an image" label which acts as the upload button
    const uploadLabel = uploadComponent.locator('label[htmlFor="file-upload"]');
    await expect(uploadLabel).toBeVisible();
  });
});
