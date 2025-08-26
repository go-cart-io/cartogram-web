describe('View cartogram', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5000/cartogram')
    cy.get('.consent-buttons > .btn-primary').click()
  })

  it('can switch to a specific map', () => {
    cy.intercept('GET', '/static/cartdata/world/data.csv').as('gotoWorld')
    cy.get('#mapSelect').select('world')
    cy.wait('@gotoWorld').its('response.statusCode').should('be.oneOf', [200, 304])
  })

  it('can switch between datasets', () => {
    cy.intercept('GET', '/static/cartdata/usa/Geographic%20Area.json').as('gotoGeographicArea')
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
        expect(text).to.contain('http://localhost:5000/cartogram/map/usa')
      })
    })
    cy.get('#clipboard-embed').click()
    cy.window().then((win) => {
      win.navigator.clipboard.readText().then((text) => {
        expect(text).to.contain('http://localhost:5000/cartogram/map/usa/embed')
      })
    })
    cy.get('#shareModal > .modal-dialog > .modal-content > .modal-header > .btn-close').click()
  })
})
