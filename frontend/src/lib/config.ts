export default function getConfig(pid: string, handler: string): boolean[] {
  let design: { [key: string]: string[] } = {
    '58': ['P', 'PZRS', 'PZR', 'PZ'],
    '23': ['PZRS', 'PZR', 'PZ', 'P'],
    '24': ['PZR', 'PZ', 'P', 'PZRS'],
    '26': ['PZ', 'P', 'PZRS', 'PZR'],
    '12': ['PZ', 'P', 'PZRS', 'PZR'],
    '27': ['P', 'PZRS', 'PZR', 'PZ'],
    '28': ['PZRS', 'PZR', 'PZ', 'P'],
    '29': ['PZR', 'PZ', 'P', 'PZRS'],
    '15': ['PZR', 'PZ', 'P', 'PZRS'],
    '32': ['PZ', 'P', 'PZRS', 'PZR'],
    '34': ['P', 'PZRS', 'PZR', 'PZ'],
    '37': ['PZRS', 'PZR', 'PZ', 'P'],
    '18': ['PZRS', 'PZR', 'PZ', 'P'],
    '30': ['PZR', 'PZ', 'P', 'PZRS'],
    '35': ['PZ', 'P', 'PZRS', 'PZR'],
    '38': ['P', 'PZRS', 'PZR', 'PZ'],
    '16': ['P', 'PZRS', 'PZR', 'PZ'],
    '45': ['PZRS', 'PZR', 'PZ', 'P'],
    '47': ['PZR', 'PZ', 'P', 'PZRS'],
    '61': ['PZ', 'P', 'PZRS', 'PZR'],
    '13': ['PZ', 'P', 'PZRS', 'PZR'],
    '22': ['P', 'PZRS', 'PZR', 'PZ'],
    '49': ['PZRS', 'PZR', 'PZ', 'P'],
    '54': ['PZR', 'PZ', 'P', 'PZRS'],
    '20': ['PZR', 'PZ', 'P', 'PZRS'],
    '41': ['PZ', 'P', 'PZRS', 'PZR'],
    '44': ['P', 'PZRS', 'PZR', 'PZ'],
    '46': ['PZRS', 'PZR', 'PZ', 'P'],
    '14': ['PZRS', 'PZR', 'PZ', 'P'],
    '39': ['PZR', 'PZ', 'P', 'PZRS'],
    '42': ['PZ', 'P', 'PZRS', 'PZR'],
    '52': ['P', 'PZRS', 'PZR', 'PZ']
  }

  let group = (parseInt(pid) - 1) % 4
  let testId = handler.replace('test', '')

  if (!design[testId]) return [true, true, true]

  let featureString = design[testId][group]
  let zoom = featureString.includes('Z')
  let rotate = featureString.includes('R')
  let stretch = featureString.includes('S')

  return [zoom, rotate, stretch]
}
