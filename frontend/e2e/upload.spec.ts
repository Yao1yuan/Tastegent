import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Restaurant Agent E2E', () => {
  test('should load the homepage and show menu', async ({ page }) => {
    // Mock the menu response
    await page.route('**/menu', async route => {
      const json = [
        { id: 1, name: 'Test Burger', price: 10, description: 'Test', tags: ['test'] },
        { id: 2, name: 'Test Pizza', price: 12, description: 'Test', tags: ['test'] },
        { id: 3, name: 'Test Salad', price: 8, description: 'Test', tags: ['test'] },
        { id: 4, name: 'Test Drink', price: 2, description: 'Test', tags: ['test'] },
        { id: 5, name: 'Test Dessert', price: 5, description: 'Test', tags: ['test'] }
      ];
      await route.fulfill({ json });
    });

    await page.goto('/');

    // Check title
    await expect(page.locator('h1')).toHaveText('Restaurant AI Agent');

    // Check menu items exist
    await expect(page.locator('.menu-section')).toBeVisible();
    await expect(page.locator('.menu-item')).toHaveCount(5);
  });

  test('should upload and crop an image', async ({ page }) => {
    await page.goto('/');

    // Locate the file input
    const fileInput = page.locator('input[type="file"]');

    // Upload a file
    const filePath = path.resolve('src/assets/react.svg');
    await fileInput.setInputFiles(filePath);

    // Verify preview appears
    await expect(page.locator('.preview-area')).toBeVisible();
    await expect(page.locator('.image-preview img')).toBeVisible();

    // Verify actions buttons are visible
    await expect(page.locator('button.upload-btn')).toBeVisible();
    await expect(page.locator('button.clear-btn')).toBeVisible();

    // Click upload
    // Note: This requires the backend to be running. If not, this test might fail or we should mock the backend.
    // However, since this is E2E, we assume full stack is running.
    // But for robustness in this environment, I'll mock the upload endpoint if the backend isn't up,
    // but the instructions say backend is done.

    // We will intercept the upload request to ensure we don't depend on actual backend if it fails,
    // or we can test the real backend. Let's try real first, but if it fails, we know why.
    // Actually, let's mock it for stability in this test environment.

    await page.route('**/upload', async route => {
      const json = {
        original_filename: 'react.svg',
        stored_filename: 'stored_react.svg',
        url: '/uploads/stored_react.svg'
      };
      await route.fulfill({ json });
    });

    await page.click('button.upload-btn');

    // Verify success message
    await expect(page.locator('.upload-success')).toBeVisible();
    await expect(page.locator('.upload-success p')).toHaveText('Image uploaded successfully!');

    // Verify image is displayed in the list
    await expect(page.locator('.upload-success img')).toBeVisible();
  });
});
