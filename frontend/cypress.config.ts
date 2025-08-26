import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    experimentalStudio: true,
    fixturesFolder: '../test-data',
    setupNodeEvents(on, config) {
      // implement node event listeners here
    }
  }
})
