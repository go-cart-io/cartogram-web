import { test, expect } from '@playwright/test'
import * as fs from 'fs'

const errors: Array<Error> = []

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:5000/cartogram')
  await page.getByRole('button', { name: 'Accept' }).click()
  page.on('pageerror', (ex) => {
    errors.push(ex)
  })
})

test.afterEach(async ({ page }) => {
  console.log(errors)
  expect(errors.length).toBe(0)
})

test('Download template data', async ({ page }) => {
  const downloadPromise = page.waitForEvent('download')
  await page.getByTitle('Download template').click()
  const download = await downloadPromise
  const filePath = './test-results/' + download.suggestedFilename()
  await download.saveAs(filePath)
  expect((await fs.promises.stat(filePath)).size).toEqual(1480)
})

test('Upload data', async ({ page }) => {
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    await page.getByTitle('Upload Data').click()
  ])
  await fileChooser.setFiles('./tests/usa_template.csv')
  await page.getByRole('button', { name: 'Yes, I Confirm' }).click()
})

test('Edit data', async ({ page }) => {
  await page.getByTitle('Edit data').click()

  await page.locator('[id="input-0-2"]').fill('90')
  await page.locator('[id="input-0-3"]').fill('#332c96')

  await page.getByRole('button', { name: 'Save changes' }).click()
  await page.getByRole('button', { name: 'Yes, I Confirm' }).click()
})

test('Interact with map', async ({ page }) => {
  await page.locator('#handler').selectOption('thailand')
  await page.getByTitle('Customization').click()
  await page.getByRole('checkbox', { name: 'Grid Lines' }).check()
  await page.getByRole('checkbox', { name: 'Resizable Legend' }).check()

  await page.getByRole('button', { name: 'Land Area' }).click()
  await page.getByRole('button', { name: 'Population' }).click()

  await page.getByTitle('Download map').click()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('link', { name: 'SVG' }).click()
  const download = await downloadPromise
  const download1Promise = page.waitForEvent('download')
  await page.getByRole('link', { name: 'GeoJSON' }).click()
  const download1 = await download1Promise
  await page.getByRole('button', { name: 'Close' }).click()

  await page.getByTitle('Download cartogram').click()
  const download2Promise = page.waitForEvent('download')
  await page.getByRole('link', { name: 'SVG' }).click()
  const download2 = await download2Promise
  const download3Promise = page.waitForEvent('download')
  await page.getByRole('link', { name: 'GeoJSON' }).click()
  const download3 = await download3Promise
  //await page.getByTitle('Copy').click()
  await page.getByRole('button', { name: 'Close' }).click()

  await page.getByTitle('Share cartogram').click()
  await page.locator('#clipboard-link').click()
  await page.getByRole('button', { name: 'Close' }).click()
})

test('Embed', async ({ page }) => {
  await page.getByTitle('Edit data').click()

  await page.locator('[id="input-0-2"]').fill('90')
  await page.locator('[id="input-0-3"]').fill('#332c96')

  await page.getByRole('button', { name: 'Save changes' }).click()
  await page.getByRole('button', { name: 'Yes, I Confirm' }).click()
  await page.getByTitle('Share cartogram').click()

  var link1 = await page.locator('#share-link-href').inputValue()
  var link2Temp = await page.locator('#share-embed-code').inputValue()
  var link2 = link2Temp.substring(13, link2Temp.indexOf('"', 14))

  await page.getByRole('button', { name: 'Close' }).click()
  await page.goto(link1)
  await page.goto(link2)
})
