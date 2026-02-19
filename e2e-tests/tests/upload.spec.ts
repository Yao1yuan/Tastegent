import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Image Upload Feature', () => {
  test('should allow user to upload an image', async ({ page }) => {
    await page.goto('/');

    // We no longer check for visibility directly, we let Playwright's auto-wait handle it.
    // The label that triggers the file input is what the user sees.
    const fileInput = page.locator('#file-upload');

    // 2. Select an image file
    // Using a relative path to the react.svg asset in the frontend folder
    // Since we are running from e2e-tests folder, we need to go up two levels
    const imagePath = path.join(__dirname, '..', '..', 'frontend', 'src', 'assets', 'react.svg');
    await fileInput.setInputFiles(imagePath);

    // 3. Verify preview is shown
    const previewImage = page.locator('.image-preview img');
    await expect(previewImage).toBeVisible();

    // 4. Click Upload button
    const uploadButton = page.getByRole('button', { name: 'Upload' });
    await expect(uploadButton).toBeVisible();
    await uploadButton.click();

    // 5. Verify success message
    const successMessage = page.locator('.upload-success');
    await expect(successMessage).toContainText('Image uploaded successfully!');

    // 6. Verify uploaded image display
    const uploadedImage = page.locator('.upload-success img');
    await expect(uploadedImage).toBeVisible();

    // 7. Verify chat message
    // The chat message should contain the filename "react.svg"
    const chatMessage = page.locator('.message.assistant').last();
    await expect(chatMessage).toContainText('I received your image: react.svg');
  });

  test('should allow user to cancel upload', async ({ page }) => {
    await page.goto('/');

    // Select file
    const fileInput = page.locator('#file-upload');
    const imagePath = path.join(__dirname, '..', '..', 'frontend', 'src', 'assets', 'react.svg');
    await fileInput.setInputFiles(imagePath);

    // Verify preview
    await expect(page.locator('.image-preview')).toBeVisible();

    // Click Cancel
    const cancelButton = page.getByRole('button', { name: 'Cancel' });
    await cancelButton.click();

    // Verify preview is gone and the upload trigger is available again.
    await expect(page.locator('.image-preview')).not.toBeVisible();
  });
});
