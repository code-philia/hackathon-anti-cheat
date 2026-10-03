import { openVisibleTarget } from "./support/e2e";
import { baseUrl } from './support/e2e';
import { expect, test } from '@playwright/test';
import { seedValue, signIn, uniqueAccount, seedAccount } from './support/e2e';

test.beforeEach(async ({ page }) => {
  await page.goto(baseUrl());
});

test('REQ-4-4: Manage Repository Files Through the Web Interface - Scenario 1', async ({ page }, testInfo) => {
  const contributor = seedAccount(testInfo, 'FILE_CONTRIBUTOR');
  const repositoryEntry = seedValue(testInfo, 'FILE_REPOSITORY_ENTRY');
  const fileName = `pw-file-${uniqueAccount().username.slice(-10)}.md`;
  const content = `Playwright content ${Date.now()}`;
  const message = `Add ${fileName}`;

  await signIn(page, contributor);
  await openVisibleTarget(page, repositoryEntry);
  await page.getByRole('button', { name: /add file/i }).click();
  await page.getByRole('menuitem', { name: /create new file/i }).click();
  await page.getByLabel(/file name/i).fill(fileName);
  await page.getByRole('textbox', { name: /file contents/i }).fill(content);
  await page.getByLabel(/commit message/i).fill(message);
  await page.getByRole('button', { name: /commit changes/i }).click();
  await expect(page.getByText(content, { exact: true })).toBeVisible();
  await page.getByRole('link', { name: /commits/i }).click();
  await expect(page.getByText(message, { exact: true })).toBeVisible();
});

test('REQ-4-4: Manage Repository Files Through the Web Interface - Scenario 2', async ({ page }, testInfo) => {
  const contributor = seedAccount(testInfo, 'FILE_CONTRIBUTOR');
  const repositoryEntry = seedValue(testInfo, 'FILE_REPOSITORY_ENTRY');
  await signIn(page, contributor);
  await openVisibleTarget(page, repositoryEntry);
  await page.getByRole('button', { name: /add file/i }).click();
  await page.getByRole('menuitem', { name: /create new file/i }).click();
  await page.getByLabel(/file name/i).fill('../invalid.md');
  await page.getByRole('textbox', { name: /file contents/i }).fill('must not be saved');
  await page.getByRole('button', { name: /commit changes/i }).click();
  await expect(page.getByText(/invalid.*path|commit message.*required/i)).toBeVisible();
});
