describe('Make cartogram', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5000/cartogram/create')
    cy.get('.consent-buttons > .btn-primary').click()
  })

  it('can create a cartogram from a predefined map', () => {
    cy.get('#mapSelect').select('world')
    cy.get('#dtable-cell-8-7').clear()
    cy.get('#dtable-cell-8-7').type('14239980190')
    cy.get('#colorDropdownBtn').click()
    cy.get('#colorDropdownList').contains('a', 'accent').click()
    cy.get('#dtable-vis-7', { timeout: 10000 }).select('Area: Cartogram')

    cy.get('#generateBtn').click()
    cy.location('pathname', { timeout: 20000 }).should('match', /\/cartogram\/key\/[^/]+\/preview$/)
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

    cy.get('#dtable-vis-7', { timeout: 10000 }).select('Area: Cartogram')
    cy.get('#dtable-vis-8', { timeout: 10000 }).select('Area: Cartogram')
    cy.get('#generateBtn').click()
  })
})
