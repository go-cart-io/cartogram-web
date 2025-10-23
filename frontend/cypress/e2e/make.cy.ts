describe('Make cartogram', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5005/create')
    cy.get('.consent-buttons > .btn-primary').click()
  })

  it('can create a cartogram from a predefined map', () => {
    cy.get('#mapSelect').select('world_by_region')
    cy.get('#dtable-cell-8-7').clear()
    cy.get('#dtable-cell-8-7').type('14239980190')
    cy.get('#colorDropdownBtn').click()
    cy.get('#colorDropdownList').contains('a', 'accent').click()
    cy.get('#dtable-vis-7', { timeout: 10000 }).select('contiguous')

    cy.get('#generateBtn').click()

    // Function that checks either the button appears or we are redirected
    const waitForResultOrRedirect = () => {
      cy.log('Waiting for result or redirect...')

      cy.get('body').then(($body) => {
        if ($body.find('#view-result-btn').length > 0) {
          cy.get('#view-result-btn').click()
        } else {
          // Retry after a short wait (polling every 5s)
          cy.wait(5000).then(waitForResultOrRedirect)
        }
      })
    }

    // Start polling (for up to 3 minutes)
    cy.wrap(null).then({ timeout: 180000 }, waitForResultOrRedirect)

    cy.location('pathname', { timeout: 20000 }).should('match', /\/view\/key\/[^/]+\/preview$/)
  })

  it('can create multiple cartograms from a geojson file', () => {
    cy.fixture('usa_by_state_since_1959.geojson', null).as('geojsonFile')
    cy.get('#geoFileInput').selectFile('@geojsonFile', { force: true })
    cy.get('#regionColSelect', { timeout: 10000 }).should('be.visible').select('State')

    cy.fixture('usa_by_state_since_1959.csv', null).as('csvFile')
    cy.get('#csvInput').selectFile('@csvFile', { force: true })

    cy.wait(2000) // wait for 2 seconds
    cy.get('#dtable-name-7', { timeout: 10000 }).should('have.value', 'Population')
    cy.get('#dtable-unit-7', { timeout: 10000 }).should('have.value', 'million people')

    cy.get('#dtable-vis-7', { timeout: 10000 }).select('contiguous')
    cy.get('#dtable-vis-8', { timeout: 10000 }).select('contiguous')
    cy.get('#generateBtn').click()
    cy.location('pathname', { timeout: 20000 }).should('match', /\/view\/key\/[^/]+\/preview$/)
  })
})
