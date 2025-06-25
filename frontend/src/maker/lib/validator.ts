import type { KeyValueArray } from './interface'
import { useProjectStore } from '../stores/project'

export function validateCSV(csvData: KeyValueArray): boolean {
  const store = useProjectStore()
  if (csvData.length === 0) return false

  // 1. Check if the CSV header contains the "Region" column.
  if (!csvData[0].hasOwnProperty('Region')) {
    // Mark error on the header for the Region field.
    const regionField = store.dataTable.fields.find((field) => field.label === 'Region')
    if (regionField) {
      regionField.errorMessage = 'Region column not found in the uploaded CSV'
      regionField.headerError = true // Custom property for header errors.
    }
    return false
  } else {
    // Clear any header error if the Region column is present.
    const regionField = store.dataTable.fields.find((field) => field.label === 'Region')
    if (regionField) {
      regionField.errorMessage = ''
      regionField.headerError = false
    }
  }

  // 2. Compare Region values row by row.
  const csvRegions = csvData.map((row) => row['Region'])
  const mapRegions = store.dataTable.items.map((row) => row['Region'])

  let valid = true

  // Check row count mismatch and mark header error.
  if (csvRegions.length !== mapRegions.length) {
    const regionField = store.dataTable.fields.find((field) => field.label === 'Region')
    if (regionField) {
      regionField.errorMessage = `Row count mismatch: CSV has ${csvRegions.length} rows, but expected ${mapRegions.length}`
      regionField.headerError = true
    }
    valid = false
  }

  // Now, check each row's Region value.
  for (let i = 0; i < Math.min(csvRegions.length, mapRegions.length); i++) {
    if (csvRegions[i] !== mapRegions[i]) {
      // Mark error on the specific row's Region cell.
      store.dataTable.items[i].regionError =
        `Region mismatch at row ${i + 1}: CSV has "${csvRegions[i]}", expected "${mapRegions[i]}"`
      valid = false
    } else {
      // Clear any previous error if the values match.
      delete store.dataTable.items[i].regionError
    }
  }

  return valid
}
