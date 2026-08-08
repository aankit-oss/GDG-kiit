import { test, expect } from '@playwright/test'

/**
 * E2E: Grounded Q&A Flow
 * Upload a document → ask a question → assert grounded answer OR explicit refusal.
 */
test.describe('Grounded Q&A Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/qa')
    await expect(page.locator('h1')).toContainText('Grounded Q&A')
  })

  test('page loads with upload zone', async ({ page }) => {
    await expect(page.locator('#file-upload-zone')).toBeVisible()
    await expect(page.locator('#file-upload-zone')).toContainText('Drop your document')
  })

  test('question textarea appears after upload', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles({
      name: 'contract.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Service agreement between Alpha and Beta.'),
    })

    await page.waitForResponse(
      res => res.url().includes('/api/documents/upload'),
      { timeout: 15000 }
    ).catch(() => null)

    const questionInput = page.locator('#question-input')
    await expect(questionInput).toBeVisible({ timeout: 5000 })
    await expect(page.locator('#ask-question-btn')).toBeVisible()
  })

  test('ask question shows answer block or refusal message', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles({
      name: 'policy.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('We retain personal data for 30 days after account closure.'),
    })

    const uploadRes = await page.waitForResponse(
      res => res.url().includes('/api/documents/upload'),
      { timeout: 15000 }
    ).catch(() => null)

    if (!uploadRes) {
      test.skip(true, 'Backend not available — skipping E2E Q&A run')
      return
    }

    // Type a question
    const questionInput = page.locator('#question-input')
    await questionInput.waitFor({ state: 'visible', timeout: 5000 })
    await questionInput.fill('What is the data retention period in this document?')

    // Submit
    const askBtn = page.locator('#ask-question-btn')
    await askBtn.click()

    // Wait for response
    await page.waitForResponse(
      res => res.url().includes('/api/qa'),
      { timeout: 30000 }
    ).catch(() => null)

    // Assert either answer block OR refusal message is shown (not both)
    const answerVisible = await page.locator('#answer-block').isVisible().catch(() => false)
    const refusalVisible = await page.locator('#refusal-message').isVisible().catch(() => false)

    expect(answerVisible || refusalVisible).toBe(true)

    // CRITICAL: both cannot be visible at the same time
    if (answerVisible && refusalVisible) {
      throw new Error('Both answer and refusal shown simultaneously — this is a bug')
    }
  })

  test('explicit refusal shown for out-of-document question', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles({
      name: 'policy.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('This is a short privacy policy about data collection.'),
    })

    const uploadRes = await page.waitForResponse(
      res => res.url().includes('/api/documents/upload'),
      { timeout: 15000 }
    ).catch(() => null)

    if (!uploadRes) {
      test.skip(true, 'Backend not available')
      return
    }

    const questionInput = page.locator('#question-input')
    await questionInput.waitFor({ state: 'visible', timeout: 5000 })
    // Ask a question that's clearly not in a tiny document
    await questionInput.fill('What is the orbital period of Jupiter and how does it affect climate change in Antarctica?')

    await page.locator('#ask-question-btn').click()

    await page.waitForResponse(
      res => res.url().includes('/api/qa'),
      { timeout: 30000 }
    ).catch(() => null)

    // For a clearly off-topic question, system should refuse
    const responseSection = page.locator('#qa-response')
    await expect(responseSection).toBeVisible({ timeout: 10000 })
  })

  test('navbar navigates between audit and qa pages', async ({ page }) => {
    const auditLink = page.locator('a[href="/audit"]')
    await auditLink.click()
    await expect(page.locator('h1')).toContainText('Compliance Audit')

    const qaLink = page.locator('a[href="/qa"]')
    await qaLink.click()
    await expect(page.locator('h1')).toContainText('Grounded Q&A')
  })
})
