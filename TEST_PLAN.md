# QA Test Plan

## Overview
This document outlines the test plan for the Restaurant Agent application.

## Test Scope
- **Backend**: API endpoints for file upload, storage, and compression.
- **Frontend**: Upload interface, preview, and image cropping functionality.
- **End-to-End (E2E)**: Full user journey from uploading an image to viewing/cropping it.

## Testing Tools
- **E2E Testing**: Playwright (Node.js)
- **Frontend Unit/Integration**: Vitest (if applicable)
- **Backend Testing**: Pytest (future consideration)

## Test Scenarios

### 1. File Upload
- **Happy Path**: User uploads a valid image (JPG/PNG).
  - Verify image is uploaded successfully.
  - Verify preview is shown.
- **Edge Cases**:
  - Upload invalid file type (e.g., .txt, .pdf).
  - Upload large file (exceeding limit).
  - Network failure during upload.

### 2. Image Processing (Compression/Storage)
- Verify uploaded image is stored in the backend.
- Verify compression is applied (check file size reduction).

### 3. Image Cropping (Frontend)
- User selects an area to crop.
- Verify cropped image is generated/previewed.
- Verify cropping coordinates are sent to backend (if applicable).

## Setup
To run tests:
1. Ensure you are in the `frontend` directory.
2. Install dependencies: `npm install` (includes Playwright).
3. Run Playwright tests: `npx playwright test`.

## Tasks
- [x] Install Playwright.
- [x] Configure Playwright.
- [x] Write E2E test scripts.
- [x] Run tests and report bugs.

## Test Results
- **Frontend E2E Tests**: Passed.
  - Homepage loads correctly.
  - Image upload flow works (mocked backend).
