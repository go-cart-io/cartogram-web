export function getOriginalMatrix(): Array<Array<number>> {
  return [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
  ]
}

export function getScaleMatrix(x: number, y: number): Array<Array<number>> {
  return [
    [x, 0, 0],
    [0, y, 0],
    [0, 0, 1]
  ]
}

export function getRotateMatrix(degree: number): Array<Array<number>> {
  return [
    [Math.cos(degree), -Math.sin(degree), 0],
    [Math.sin(degree), Math.cos(degree), 0],
    [0, 0, 1]
  ]
}

export function getTranslateMatrix(x: number, y: number): Array<Array<number>> {
  return [
    [1, 0, x],
    [0, 1, y],
    [0, 0, 1]
  ]
}

export function multiplyMatrix(
  matrix1: Array<Array<number>>,
  matrix2: Array<Array<number>>
): Array<Array<number>> {
  if (matrix1.length !== 3 || matrix2.length !== 3) {
    throw new Error('Both matrices should be 3x3.')
  }

  const result = [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0]
  ]

  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      for (let k = 0; k < 3; k++) {
        result[i][j] += matrix1[i][k] * matrix2[k][j]
      }
    }
  }

  return result
}
