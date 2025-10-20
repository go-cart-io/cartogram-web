import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CColorLegend from '@/common/components/CColorLegend.vue'

describe('CColorLegend', () => {
  it('renders legend and dropdown', () => {
    const wrapper = mount(CColorLegend, {
      props: {
        colorFields: ['Population', 'Density'],
        currentColorCol: 'Region'
      }
    })
    // Legend container exists
    expect(wrapper.find('#color-legend').exists()).toBe(true)
    // Dropdown button exists
    expect(wrapper.find('.dropdown-toggle').exists()).toBe(true)
    // Region option is present and active
    const regionBtn = wrapper.findAll('.dropdown-item').find((btn) => btn.text().includes('Region'))
    expect(regionBtn).toBeTruthy()
    expect(regionBtn?.classes()).toContain('active')
    // Data label and color fields
    expect(wrapper.text()).toContain('Data:')
    expect(wrapper.text()).toContain('Population')
    expect(wrapper.text()).toContain('Density')
  })

  it('emits change event when color field is clicked', async () => {
    const wrapper = mount(CColorLegend, {
      props: {
        colorFields: ['Population', 'Density'],
        currentColorCol: 'Region'
      }
    })
    const popBtn = wrapper
      .findAll('.dropdown-item')
      .find((btn) => btn.text().includes('Population'))
    await popBtn?.trigger('click')
    expect(wrapper.emitted('change')).toBeTruthy()
    expect(wrapper.emitted('change')![0]).toEqual(['Population'])
  })

  it('shows disabled message if no colorFields', () => {
    const wrapper = mount(CColorLegend, {
      props: {
        colorFields: [],
        currentColorCol: 'Region'
      }
    })
    expect(wrapper.text()).toContain('No color column')
  })
})
