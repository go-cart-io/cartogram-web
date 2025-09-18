import { describe, it, expect } from 'vitest'
import * as util from '@/maker/lib/util'
import type { KeyValueArray } from '@/maker/lib/interface'

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
      const data: KeyValueArray = []
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

  describe('copyKeyInArray', () => {
    it('should copy the value from formKey to toKey for each object where formKey exists', () => {
      const data = [
        { a: 1, b: 2 },
        { a: 3, b: 4 }
      ]
      const result = util.copyKeyInArray(data, 'a', 'c')
      expect(result).toEqual([
        { a: 1, b: 2, c: 1 },
        { a: 3, b: 4, c: 3 }
      ])
    })

    it('should not add toKey if formKey does not exist in the object', () => {
      const data = [
        { x: 10, y: 20 },
        { a: 5, b: 6 }
      ]
      const result = util.copyKeyInArray(data, 'a', 'z')
      expect(result).toEqual([
        { x: 10, y: 20 },
        { a: 5, b: 6, z: 5 }
      ])
    })

    it('should handle empty array', () => {
      const data: any[] = []
      const result = util.copyKeyInArray(data, 'foo', 'bar')
      expect(result).toEqual([])
    })

    it('should copy undefined if formKey exists but value is undefined', () => {
      const data = [{ foo: undefined, bar: 1 }]
      const result = util.copyKeyInArray(data, 'foo', 'baz')
      expect(result).toEqual([{ foo: undefined, bar: 1, baz: undefined }])
    })

    it('should not mutate the original array', () => {
      const data = [{ a: 1 }]
      const copy = JSON.parse(JSON.stringify(data))
      util.copyKeyInArray(data, 'a', 'b')
      expect(data).toEqual(copy)
    })
  })

  describe('filterKeyValueInArray', () => {
    it('should filter objects to only include properties of the Number type and of the except', () => {
      const data = [
        { name: 'Alice', age: 30, active: true },
        { name: 'Bob', age: 'unknown', active: false },
        { name: 'Cat', age: '25', active: false }
      ]
      const except = ['name']
      const result = util.filterKeyValueInArray(data, except)
      expect(result).toEqual([
        { name: 'Alice', age: 30 },
        { name: 'Bob' },
        { name: 'Cat', age: 25 }
      ])
    })

    it('should filter objects to only include properties of the except', () => {
      const data = [
        { name: 'Alice', age: 30, active: true },
        { name: 'Bob', age: 'unknown', active: false },
        { name: 'Cat', age: '25', active: false }
      ]
      const except = ['name']
      const result = util.filterKeyValueInArray(data, except, null)
      expect(result).toEqual([{ name: 'Alice' }, { name: 'Bob' }, { name: 'Cat' }])
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
      const templateKeys: string[] = []
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

  describe('updateObjInArray', () => {
    const baseData = [
      { id: 1, name: 'A', value: 10 },
      { id: 2, name: 'B', value: 20 },
      { id: 3, name: 'C', value: 30 }
    ]
    const newData = [
      { id: 2, name: 'B2', value: 200, extra: true },
      { id: 3, name: 'C2', value: 300 },
      { id: 4, name: 'D', value: 400 }
    ]

    it('should update matching objects and track unmatched', () => {
      const result = util.updateObjInArray(baseData, newData, 'id')
      expect(result.updated).toEqual([
        { id: 1, name: 'A', value: 10 },
        { id: 2, name: 'B2', value: 200, extra: true },
        { id: 3, name: 'C2', value: 300 }
      ])
      expect(result.fields).toEqual(['id', 'name', 'value', 'extra'])
      expect(result.unupdatedIndex).toEqual([0])
      expect(result.unmatched).toEqual([{ id: 4, name: 'D', value: 400 }])
    })

    it('should handle empty newData', () => {
      const result = util.updateObjInArray(baseData, [], 'id')
      expect(result.updated).toEqual(baseData)
      expect(result.fields).toEqual([])
      expect(result.unupdatedIndex).toEqual([0, 1, 2])
      expect(result.unmatched).toEqual([])
    })

    it('should handle empty baseData', () => {
      const result = util.updateObjInArray([], newData, 'id')
      expect(result.updated).toEqual([])
      expect(result.fields).toEqual([])
      expect(result.unupdatedIndex).toEqual([])
      expect(result.unmatched).toEqual(newData)
    })

    it('should not mutate input arrays', () => {
      const baseCopy = JSON.parse(JSON.stringify(baseData))
      const newCopy = JSON.parse(JSON.stringify(newData))
      util.updateObjInArray(baseData, newData, 'id')
      expect(baseData).toEqual(baseCopy)
      expect(newData).toEqual(newCopy)
    })
  })

  describe('getNameUnit', () => {
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
})
