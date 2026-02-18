import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Restaurant AI Agent/);
});

test('menu loads', async ({ page }) => {
  await page.goto('/');

  // Check if menu section exists
  await expect(page.locator('.menu-section')).toBeVisible();

  // Check if at least one menu item is displayed
  // We might need to wait for data loading
  await expect(page.locator('.menu-item').first()).toBeVisible();
});
