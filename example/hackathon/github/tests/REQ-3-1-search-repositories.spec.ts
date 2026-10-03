import { expect, test } from '@playwright/test';
import { baseUrl, seedValue } from './support/e2e';

test.beforeEach(async ({ page }) => {
  await page.goto(baseUrl());
});

test('REQ-3-1: Search for and Locate Repositories - Scenario 1', async ({ page }, testInfo) => {
  const repositoryName = seedValue(testInfo, 'PUBLIC_REPOSITORY_NAME');

  await page.goto(baseUrl());
  await page.getByRole('searchbox', { name: 'Search', exact: true }).fill(repositoryName);
  await page.getByRole('searchbox', { name: 'Search', exact: true }).press('Enter');
  await page.getByRole('link', { name: repositoryName, exact: true }).click();

  await expect(page.getByRole('heading', { name: new RegExp(repositoryName, 'i') })).toBeVisible();
});

test('REQ-3-1: Search for and Locate Repositories - Scenario 2', async ({ page }, testInfo) => {
  const privateRepositoryName = seedValue(testInfo, 'PRIVATE_REPOSITORY_NAME');

  await page.goto(baseUrl());
  await page.getByRole('searchbox', { name: 'Search', exact: true }).fill(privateRepositoryName);
  await page.getByRole('searchbox', { name: 'Search', exact: true }).press('Enter');

  await expect(page.getByRole('link', { name: privateRepositoryName, exact: true })).not.toBeVisible();
});

test('REQ-3-1: Search for and Locate Repositories - Scenario 3', async ({ page }) => {
  const query = `no-repository-${Date.now()}`;
  await page.goto(baseUrl());
  await page.getByRole('searchbox', { name: 'Search', exact: true }).fill(query);
  await page.getByRole('searchbox', { name: 'Search', exact: true }).press('Enter');
  await expect(page.getByText(/no repositories|no results/i)).toBeVisible();
});

test('REQ-3-1: Search for and Locate Repositories - Scenario 4', async ({ page }, testInfo) => {
  const repositoryName = seedValue(testInfo, 'PUBLIC_REPOSITORY_NAME');

  await page.goto(baseUrl());
  await page.getByRole('searchbox', { name: 'Search', exact: true }).fill(repositoryName);
  await page.getByRole('searchbox', { name: 'Search', exact: true }).press('Enter');
  await page.getByRole('link', { name: repositoryName, exact: true }).click();
  await expect(page.getByRole('heading', { name: new RegExp(repositoryName, 'i') })).toBeVisible();

  await page.reload();
  await expect(page.getByRole('heading', { name: new RegExp(repositoryName, 'i') })).toBeVisible();
});
