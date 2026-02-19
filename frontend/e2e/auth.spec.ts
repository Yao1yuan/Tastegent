import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should allow a user to log in and redirect to the admin page', async ({ page }) => {
    // Mock the token response
    await page.route('**/token', async route => {
      const json = {
        access_token: 'fake-jwt-token',
        token_type: 'bearer'
      };
      await route.fulfill({ json });
    });

    // Mock the menu response for the admin page
    await page.route('**/menu', async route => {
        const json = [
          { id: 1, name: 'Admin Burger', price: 10, description: 'Test', tags: ['test'] }
        ];
        await route.fulfill({ json });
      });

    // Go to the login page
    await page.goto('/login');

    // Fill in the login form
    await page.locator('input[placeholder="Username"]').fill('admin');
    await page.locator('input[placeholder="Password"]').fill('password');

    // Click the login button
    await page.locator('button[type="submit"]').click();

    // Wait for navigation to the admin page
    await page.waitForURL('/admin');

    // Check that the user is on the admin page
    await expect(page.locator('h1')).toHaveText('Menu Management');

    // Check that the token is in localStorage
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBe('fake-jwt-token');
  });

  test('should show an error for invalid credentials', async ({ page }) => {
    // Mock the token response for failure
    await page.route('**/token', async route => {
      await route.fulfill({
        status: 401,
        json: { detail: 'Incorrect username or password' }
      });
    });

    // Go to the login page
    await page.goto('/login');

    // Fill in the login form with wrong credentials
    await page.locator('input[placeholder="Username"]').fill('wrong');
    await page.locator('input[placeholder="Password"]').fill('wrong');

    // Click the login button
    await page.locator('button[type="submit"]').click();

    // Check that an error message is displayed
    const errorMessage = page.locator('p[style="color: red;"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toHaveText('Invalid username or password');

    // Check that the user is still on the login page
    expect(page.url()).toContain('/login');
  });
});
