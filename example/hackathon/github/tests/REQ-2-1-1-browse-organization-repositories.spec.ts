import { baseUrl } from './support/e2e';
import { expect, test } from '@playwright/test';
import { seedValue, openVisibleOrganization } from './support/e2e';

test.beforeEach(async ({ page }) => {
  await page.goto(baseUrl());
});

test('REQ-2-1-1: Browse Organization Repositories - Scenario 1', async ({ page }, testInfo) => {
  const organizationName = seedValue(testInfo, 'EXISTING_ORGANIZATION');
  const repositoryName = seedValue(testInfo, 'PUBLIC_ORGANIZATION_REPOSITORY');

  await openVisibleOrganization(page, organizationName);
  await page.getByRole('link', { name: 'Repositories', exact: true }).click();
  await page.getByRole('textbox', { name: 'Find a repository', exact: true }).fill(repositoryName);
  await page.getByRole('link', { name: repositoryName, exact: true }).click();

  await expect(page.getByRole('heading', { name: new RegExp(repositoryName, 'i') })).toBeVisible();
  await page.getByRole('link', { name: organizationName, exact: true }).click();
  await page.getByRole('link', { name: 'Repositories', exact: true }).click();
  await expect(page.getByRole('link', { name: repositoryName, exact: true })).toBeVisible();
});

test('REQ-2-1-1: Browse Organization Repositories - Scenario 2', async ({ page }, testInfo) => {
  const organizationName = seedValue(testInfo, 'EXISTING_ORGANIZATION');
  const privateRepositoryName = seedValue(testInfo, 'PRIVATE_ORGANIZATION_REPOSITORY');

  await openVisibleOrganization(page, organizationName);
  await page.getByRole('link', { name: 'Repositories', exact: true }).click();
  await page.getByRole('textbox', { name: 'Find a repository', exact: true }).fill(privateRepositoryName);

  await expect(page.getByRole('link', { name: privateRepositoryName, exact: true })).not.toBeVisible();
});
