export const NICE_NUMBERS = [1, 2, 5, 10, 20, 50]
export function findNearestNiceNumber(value: number): [number, number] {
  let scaleNiceNumber = 99
  const scalePowerOf10 = Math.floor(Math.log10(value))

  // We find the "nice number" that is closest to valuePerSquare's
  const valueFirstNumber = value / Math.pow(10, scalePowerOf10)
  let valueDiff = Math.abs(valueFirstNumber - scaleNiceNumber)
  NICE_NUMBERS.forEach(function (n) {
    if (Math.abs(valueFirstNumber - n) < valueDiff) {
      valueDiff = Math.abs(valueFirstNumber - n)
      scaleNiceNumber = n
    }
  })

  return [scaleNiceNumber, scalePowerOf10]
}
