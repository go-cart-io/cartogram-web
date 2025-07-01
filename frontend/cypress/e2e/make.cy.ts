describe('Make cartogram', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5000/cartogram/create')
    cy.get('.consent-buttons > .btn-primary').click()
  })

  it('can create a cartogram from a predefined map', () => {
    cy.get('#mapSelect').select('world')
    cy.get(':nth-child(38) > :nth-child(7) > .cell-content > .form-control').clear()
    cy.get(':nth-child(38) > :nth-child(7) > .cell-content > .form-control').type('14239980190')
    cy.get('#colorDropdownBtn').click()
    cy.get('#colorDropdownList').contains('a', 'accent').click()

    cy.intercept('PUT', '/cartogram/key', {}).as('viewUrl')
    cy.get('#generateBtn').click()
    cy.wait('@viewUrl', { requestTimeout: 20000 }).its('request.url').should('include', 'preview')
  })

  it('can create multiple cartograms from a geojson file', () => {
    cy.fixture('usa_by_state_since_1959.geojson', null).as('geojsonFile')
    cy.get('#geoFileInput').selectFile('@geojsonFile', { force: true })
    cy.get('#regionColSelect', { timeout: 10000 }).should('be.visible').select('Region')

    cy.fixture('usa_by_state_since_1959.csv', null).as('csvFile')
    cy.get('#csvInput').selectFile('@csvFile', { force: true })

    cy.get('.d-table', { timeout: 10000 }).should('not.include.text', 'Shape_Area')
    cy.wait(2000) // wait for 2 seconds
    cy.get('.d-table', { timeout: 10000 }).should('include.text', 'Population')

    cy.get(':nth-child(9) > .header-cell > div > .position-absolute').click()
    cy.get('#generateBtn').click()
  })
})
