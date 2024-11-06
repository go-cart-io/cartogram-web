import { describe, it, expect } from 'vitest'
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
})
