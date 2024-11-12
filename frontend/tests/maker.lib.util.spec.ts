import { describe, it, expect } from 'vitest'
import type { FeatureCollection } from 'geojson'
import * as util from '../src/maker/lib/util'

describe('maker.lib.util', () => {
  describe('renameKeyInArray', () => {
    it('should rename the specified key in each object when the old key exists', () => {
      const data = [
        { oldKey: 'value1', anotherKey: 'value2' },
        { oldKey: 'value3', anotherKey: 'value4' }
      ]
      const result = util.renameKeyInArray(data, 'oldKey', 'newKey')
      expect(result).toEqual([
        { newKey: 'value1', anotherKey: 'value2' },
        { newKey: 'value3', anotherKey: 'value4' }
      ])
    })

    it('should return an empty array when input is an empty array', () => {
      const data = []
      const result = util.renameKeyInArray(data, 'oldKey', 'newKey')
      expect(result).toEqual([])
    })
  })

  describe('addKeyInArray', () => {
    it('should add a new key with the default value to each object in the array', () => {
      const data = [{ name: 'Alice' }, { name: 'Bob' }]
      const keyName = 'age'
      const defaultValue = 30
      const result = util.addKeyInArray(data, keyName, defaultValue)
      expect(result).toEqual([
        { name: 'Alice', age: 30 },
        { name: 'Bob', age: 30 }
      ])
    })

    it('should not add a new key if the key already exists in an object in the array', () => {
      const data = [{ name: 'Alice' }, { name: 'Bob', age: 50 }]
      const keyName = 'age'
      const defaultValue = 30
      const result = util.addKeyInArray(data, keyName, defaultValue)
      expect(result).toEqual([
        { name: 'Alice', age: 30 },
        { name: 'Bob', age: 50 }
      ])
    })
  })

  describe('filterNumberInArray', () => {
    it('should filter objects to only include properties of the Number type and of the except', () => {
      const data = [
        { name: 'Alice', age: 30, active: true },
        { name: 'Bob', age: 'unknown', active: false },
        { name: 'Cat', age: '25', active: false }
      ]
      const type = 'number'
      const except = ['name']
      const result = util.filterNumberInArray(data, except)
      expect(result).toEqual([
        { name: 'Alice', age: 30 },
        { name: 'Bob' },
        { name: 'Cat', age: 25 }
      ])
    })
  })

  describe('arrangeKeysInArray', () => {
    it('should return data with keys ordered according to templateKeys', () => {
      const templateKeys = ['name', 'age', 'race']
      const data = [
        { age: 30, name: 'Alice', location: 'Wonderland', sex: 'F' },
        { name: 'Bob', age: 25, location: 'Builderland', sex: 'M' }
      ]
      const expected = [
        { name: 'Alice', age: 30, race: null, location: 'Wonderland', sex: 'F' },
        { name: 'Bob', age: 25, race: null, location: 'Builderland', sex: 'M' }
      ]
      const result = util.arrangeKeysInArray(data, templateKeys)
      expect(result).toEqual(expected)
    })

    it('should return data unchanged when templateKeys is empty', () => {
      const templateKeys = []
      const data = [
        { age: 30, name: 'Alice', location: 'Wonderland' },
        { name: 'Bob', age: 25, location: 'Builderland' }
      ]
      const expected = [
        { age: 30, name: 'Alice', location: 'Wonderland' },
        { name: 'Bob', age: 25, location: 'Builderland' }
      ]
      const result = util.arrangeKeysInArray(data, templateKeys)
      expect(result).toEqual(expected)
    })
  })

  describe('arrangeKeysInArray', () => {
    it('should extract unit from label when enclosed in parentheses', () => {
      const label = 'Temperature (Celsius)'
      const [name, unit] = util.getNameUnit(label)
      expect(name).toBe('Temperature')
      expect(unit).toBe('Celsius')
    })

    it('should return the label when unit is empty', () => {
      const label = 'Temperature'
      const [name, unit] = util.getNameUnit(label)
      expect(name).toBe('Temperature')
      expect(unit).toBe('')
    })
  })

  describe('arrangeKeysInArray', () => {
    it('should filter properties of each feature in a GeoJSON object', () => {
      const geojson = {
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: {
              cartogram_id: 1,
              region: 'Feature 1',
              label: 'Label 1',
              other_property: 'value'
            },
            geometry: {
              type: 'Point',
              coordinates: [102.0, 0.5]
            }
          }
        ]
      } as FeatureCollection
      const result = util.filterGeoJSONProperties(
        geojson,
        ['cartogram_id', 'region', 'label'],
        ['cartogram_id', 'name', 'label']
      )
      expect(result.features[0].properties).toEqual({
        cartogram_id: 1,
        name: 'Feature 1',
        label: 'Label 1'
      })
    })
  })
})
