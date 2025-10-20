describe('View cartogram', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5005/view')
    cy.get('.consent-buttons > .btn-primary').click()
  })

  it('can switch to a specific map', () => {
    cy.intercept('GET', '/static/cartdata/world_by_region/data.csv').as('gotoWorld')
    cy.get('#mapSelect').select('world_by_region')
    cy.wait('@gotoWorld').its('response.statusCode').should('be.oneOf', [200, 304])
  })

  it('can switch between datasets', () => {
    cy.intercept(
      'GET',
      '/static/cartdata/conterminous_usa_by_state_since_1959/Geographic%20Area.json'
    ).as('gotoGeographicArea')
    cy.get('#c-area2toV0Btn').click()
    cy.wait('@gotoGeographicArea').its('response.statusCode').should('be.oneOf', [200, 304])
    cy.get('#c-area2toV1Btn').click()
  })

  it('can download svg, geojson, and data', () => {
    cy.get('#c-area2DownloadBtn').click()
    cy.get('#downloadModal1 a').contains('SVG').click()
    cy.readFile('cypress/downloads/Population.svg').should('exist')
    cy.get('#downloadModal1 a').contains('GeoJSON').click()
    cy.readFile('cypress/downloads/Population_simplified.json').should('exist')
    cy.get('#downloadModal1 a').contains('CSV').click()
    cy.readFile('cypress/downloads/data.csv').should('exist')
    cy.get('#downloadModal1 > .modal-dialog > .modal-content > .modal-header > .btn-close').click()
  })

  it('can copy share and embed link to clipboard', () => {
    cy.get('#shareBtn').click()
    cy.get('#clipboard-link').click()
    cy.window().then((win) => {
      win.navigator.clipboard.readText().then((text) => {
        expect(text).to.contain(
          'http://localhost:5005/view/map/conterminous_usa_by_state_since_1959'
        )
      })
    })
    cy.get('#clipboard-embed').click()
    cy.window().then((win) => {
      win.navigator.clipboard.readText().then((text) => {
        expect(text).to.contain(
          'http://localhost:5005/view/map/conterminous_usa_by_state_since_1959/embed'
        )
      })
    })
    cy.get('#shareModal > .modal-dialog > .modal-content > .modal-header > .btn-close').click()
  })
})
