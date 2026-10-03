import { expect, test } from '@playwright/test';
import { openAccountAccess } from './support/e2e';

async function createAccount(page: import('@playwright/test').Page) {
  const account = {
    username: 'recovery-demo',
    email: 'recovery.demo@example.test',
    password: 'Valid-password-123!',
  };
  await openAccountAccess(page);
  await page.getByRole('link', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Create an account', exact: true }).click();
  await page.getByLabel('Username', { exact: true }).fill(account.username);
  await page.getByLabel('Email', { exact: true }).fill(account.email);
  await page.getByLabel('Password', { exact: true }).fill(account.password);
  await page.getByLabel('Confirm password', { exact: true }).fill(account.password);
  await page.getByRole('checkbox', { name: 'Agree to the terms', exact: true }).check();
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  return account;
}

async function openResetStep(page: import('@playwright/test').Page, email: string): Promise<void> {
  await openAccountAccess(page);
  await page.getByRole('link', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Forgot password', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByRole('button', { name: 'Send reset link', exact: true }).click();
  await expect(page.getByText('123456', { exact: true })).toBeVisible();
  await expect(page.getByLabel('New password', { exact: true })).toBeVisible();
}

test('REQ-1-1-3: Recover Account Access Through a Verified Email - Scenario 1', async ({ page }) => {
  const account = await createAccount(page);

  await openResetStep(page, account.email);
  await expect(page.getByLabel('Verification code', { exact: true })).toBeVisible();

  await openResetStep(page, 'unknown@example.test');
  await expect(page.getByLabel('Verification code', { exact: true })).toBeVisible();
});

test('REQ-1-1-3: Recover Account Access Through a Verified Email - Scenario 2', async ({ page }) => {
  const account = await createAccount(page);
  const attemptedPassword = 'Replacement-password-456!';

  await openResetStep(page, account.email);
  await page.getByLabel('Verification code', { exact: true }).fill('000000');
  await page.getByLabel('New password', { exact: true }).fill(attemptedPassword);
  await page.getByLabel('Confirm password', { exact: true }).fill(attemptedPassword);
  await page.getByRole('button', { name: 'Reset password', exact: true }).click();
  await expect(page.getByText('Verification code is invalid', { exact: true })).toBeVisible();

  await openAccountAccess(page);
  await page.getByRole('link', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Username or email', { exact: true }).fill(account.email);
  await page.getByLabel('Password', { exact: true }).fill(account.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByText(account.username, { exact: true })).toBeVisible();
});

test('REQ-1-1-3: Recover Account Access Through a Verified Email - Scenario 3', async ({ page }) => {
  const account = await createAccount(page);
  const newPassword = 'Replacement-password-456!';

  await openResetStep(page, account.email);
  await page.getByLabel('Verification code', { exact: true }).fill('123456');
  await page.getByLabel('New password', { exact: true }).fill(newPassword);
  await page.getByLabel('Confirm password', { exact: true }).fill(newPassword);
  await page.getByRole('button', { name: 'Reset password', exact: true }).click();
  await expect(page.getByText('Password updated', { exact: true })).toBeVisible();

  await openAccountAccess(page);
  await page.getByRole('link', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Username or email', { exact: true }).fill(account.email);
  await page.getByLabel('Password', { exact: true }).fill(newPassword);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByText(account.username, { exact: true })).toBeVisible();
});
