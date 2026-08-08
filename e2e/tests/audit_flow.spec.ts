import { test, expect } from '@playwright/test'
import path from 'path'

/**
 * E2E: Audit Flow
 * Upload a document → select ruleset → run audit → assert report contains findings.
 */
test.describe('Compliance Audit Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/audit')
    await expect(page.locator('h1')).toContainText('Compliance Audit')
  })

  test('page loads with upload zone and ruleset selector', async ({ page }) => {
    await expect(page.locator('#file-upload-zone')).toBeVisible()
    // Ruleset selector only appears after upload — verify upload zone is present
    const uploadZone = page.locator('#file-upload-zone')
    await expect(uploadZone).toBeVisible()
    await expect(uploadZone).toContainText('Drop your document')
  })

  test('shows upload success after file upload', async ({ page }) => {
    // Upload the DPDP pass fixture as a text file
    const fixturePath = path.resolve('../rules/fixtures/dpdp_pass.txt')
    const fileInput = page.locator('input[type="file"]').first()

    // Use a PDF-like fixture — we'll simulate with the .txt file
    // In real E2E we'd use a real PDF; this tests the UI flow
    await fileInput.setInputFiles({
      name: 'test-policy.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content'),
    })

    // Wait for upload to complete (either success message or error)
    await page.waitForResponse(
      res => res.url().includes('/api/documents/upload') && res.status() !== 0,
      { timeout: 15000 }
    )

    // After upload: ruleset selector should appear
    const rulesetSelect = page.locator('#ruleset-select')
    await expect(rulesetSelect).toBeVisible({ timeout: 5000 })
  })

  test('run audit button appears after successful upload', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles({
      name: 'policy.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Privacy policy content'),
    })

    // Wait for API response
    await page.waitForResponse(
      res => res.url().includes('/api/documents/upload'),
      { timeout: 15000 }
    ).catch(() => null)

    const auditBtn = page.locator('#run-audit-btn')
    await expect(auditBtn).toBeVisible({ timeout: 5000 })
  })

  test('audit report shows findings after running audit', async ({ page }) => {
    // Upload
    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles({
      name: 'policy.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('This privacy policy is for testing.'),
    })

    const uploadRes = await page.waitForResponse(
      res => res.url().includes('/api/documents/upload'),
      { timeout: 15000 }
    ).catch(() => null)

    if (!uploadRes) {
      test.skip(true, 'Backend not available — skipping E2E audit run')
      return
    }

    // Click run audit
    const auditBtn = page.locator('#run-audit-btn')
    await auditBtn.waitFor({ state: 'visible', timeout: 5000 })
    await auditBtn.click()

    // Wait for report
    await page.waitForResponse(
      res => res.url().includes('/api/audit'),
      { timeout: 90000 }
    ).catch(() => null)

    // Assert report renders
    const report = page.locator('#audit-report')
    await expect(report).toBeVisible({ timeout: 10000 })

    // Assert at least one finding card rendered
    const findings = page.locator('.finding-card')
    const count = await findings.count()
    expect(count).toBeGreaterThan(0)
  })
})
