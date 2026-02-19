import { test, expect } from '@playwright/test';

test.describe('Admin CRUD Operations', () => {
  const menuItem = {
    name: `E2E Test Burger ${Date.now()}`,
    description: 'A burger created by an automated test',
    price: '15.99',
    tags: 'e2e, test, burger',
    updatedPrice: '99.99'
  };

  test.beforeEach(async ({ page }) => {
    // Navigate to login page and log in
    await page.goto('http://localhost:5173/login');
    await page.fill('input[placeholder="Username"]', 'admin');
    await page.fill('input[placeholder="Password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('http://localhost:5173/admin');
  });

  test('should allow an admin to create, read, update, and delete a menu item', async ({ page }) => {
    // CREATE
    await page.fill('input[name="name"]', menuItem.name);
    await page.fill('input[name="description"]', menuItem.description);
    await page.fill('input[name="price"]', menuItem.price);
    await page.fill('input[name="tags"]', menuItem.tags);
    await page.click('.new-item-form button[type="submit"]');

    // READ (Verify creation)
    await expect(page.locator('.menu-items')).toContainText(menuItem.name);
    await expect(page.locator('.menu-items')).toContainText(menuItem.description);
    await expect(page.locator('.menu-items')).toContainText(`$${parseFloat(menuItem.price).toFixed(2)}`);

    const menuItemSelector = `.admin-menu-item:has-text("${menuItem.name}")`;
    const createdItem = page.locator(menuItemSelector);
    await expect(createdItem).toBeVisible();

    // UPDATE
    await createdItem.locator('button:has-text("Edit")').click();
    const priceInput = createdItem.locator('input[name="price"]');
    await priceInput.fill(menuItem.updatedPrice);
    await createdItem.locator('button:has-text("Save")').click();

    // READ (Verify update)
    await expect(createdItem.locator('.price')).toContainText(`$${parseFloat(menuItem.updatedPrice).toFixed(2)}`);

    // DELETE
    page.on('dialog', dialog => dialog.accept()); // Automatically accept confirmation dialog
    await createdItem.locator('button:has-text("Delete")').click();

    // READ (Verify deletion)
    await expect(page.locator(menuItemSelector)).not.toBeVisible();
  });
});
