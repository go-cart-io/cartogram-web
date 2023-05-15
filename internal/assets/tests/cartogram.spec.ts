import { test, expect } from '@playwright/test';
import * as fs from 'fs';

const errors = [];

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:5000/cartogram');  
  page.on("pageerror", (ex) => {
    errors.push(ex);
  });
});

test.afterEach(async ({ page }) => {
  console.log(errors);
  expect(errors.length).toBe(0);
});

test('Download template data', async ({ page }) => {
  await page.getByText('Download Template Data CSV File Excel File').hover();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'CSV File' }).click();
  const download = await downloadPromise;
  const filePath = './test-results/' + download.suggestedFilename()
  await download.saveAs(filePath);
  expect((await fs.promises.stat(filePath)).size).toEqual(1480);

  await page.getByText('Download Template Data CSV File Excel File').hover();
  const downloadPromise2 = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Excel File' }).click();
  const download2 = await downloadPromise2;
  const filePath2 = './test-results/' + download2.suggestedFilename()
  await download2.saveAs(filePath2);
  expect((await fs.promises.stat(filePath2)).size).toEqual(24223);
});

test('Upload data', async ({ page }) => {
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    await page.getByRole('button', { name: 'Upload Data' }).click(),
  ])
  await fileChooser.setFiles('./tests/usa_template.csv');
  await page.getByRole('button', { name: 'Yes, I Confirm' }).click();
});

test('Edit data', async ({ page }) => {
  const page1Promise = page.waitForEvent('popup');
  await page.getByRole('button', { name: 'Edit' }).click();
  const page1 = await page1Promise;

  // set number
  await page1.getByRole('row', { name: 'Alabama 4780127 9' }).getByText('9').click();
  await page1.locator('#input-2-1').fill('10');

  // set color
  await page1.locator('#cell-3-1 div').click();
  await page1.locator('#color-selector').type('#FF0000');  

  await page1.getByText('Update').click();
  await page1.close();
  await page.getByRole('button', { name: 'Yes, I Confirm' }).click();
});

test('Interact with map', async ({ page }) => {
  await page.locator('#handler').selectOption('thailand');
  await page.locator('#map-customise').click();
  await page.getByRole('checkbox', { name: 'Show Grid Lines' }).check();
  await page.getByRole('checkbox', { name: 'Resizable Legend' }).check();
  await page.locator('#cartogram-customise').click();
  await page.locator('#gridline-toggle-cartogram').check();
  await page.locator('#legend-toggle-cartogram').check();

  await page.locator('#map2-switch-buttons').getByRole('combobox').selectOption('1-conventional');
  await page.locator('#map2-switch-buttons').getByRole('combobox').selectOption('2-population');
  await page.locator('#map-download').click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download SVG' }).click();
  const download = await downloadPromise;
  const download1Promise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download GeoJSON' }).click();
  const download1 = await download1Promise;
  await page.getByRole('button', { name: 'Close' }).click();
  await page.locator('#cartogram-download').click();
  const download2Promise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download SVG' }).click();
  const download2 = await download2Promise;
  const download3Promise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download GeoJSON' }).click();
  const download3 = await download3Promise;
  await page.getByRole('button', { name: 'Copy button' }).click();
  await page.getByRole('button', { name: 'Close' }).click();
  await page.getByRole('link', { name: 'Share' }).click();
  await page.locator('#clipboard-link').click();
  await page.getByRole('button', { name: 'Close' }).click();
});