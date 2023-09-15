export default function getConfig(pid: string, handler: string): boolean[] {
  let design: { [key: string]: string[] } = {
    '42': ['P', 'PZRS', 'PZR', 'PZ'],
    '23': ['PZRS', 'PZR', 'PZ', 'P'],
    '15': ['PZR', 'PZ', 'P', 'PZRS'],
    '26': ['PZ', 'P', 'PZRS', 'PZR'],
    '47': ['PZ', 'P', 'PZRS', 'PZR'],
    '16': ['P', 'PZRS', 'PZR', 'PZ'],
    '28': ['PZRS', 'PZR', 'PZ', 'P'],
    '39': ['PZR', 'PZ', 'P', 'PZRS'],
    '34': ['PZR', 'PZ', 'P', 'PZRS'],
    '117': ['PZ', 'P', 'PZRS', 'PZR'],
    '130': ['P', 'PZRS', 'PZR', 'PZ'],
    '138': ['PZRS', 'PZR', 'PZ', 'P'],
    '18': ['PZRS', 'PZR', 'PZ', 'P'],
    '21': ['PZR', 'PZ', 'P', 'PZRS'],
    '105': ['PZ', 'P', 'PZRS', 'PZR'],
    '64': ['P', 'PZRS', 'PZR', 'PZ'],
    '109': ['P', 'PZRS', 'PZR', 'PZ'],
    '45': ['PZRS', 'PZR', 'PZ', 'P'],
    '147': ['PZR', 'PZ', 'P', 'PZRS'],
    '132': ['PZ', 'P', 'PZRS', 'PZR'],
    '13': ['PZ', 'P', 'PZRS', 'PZR'],
    '22': ['P', 'PZRS', 'PZR', 'PZ'],
    '115': ['PZRS', 'PZR', 'PZ', 'P'],
    '54': ['PZR', 'PZ', 'P', 'PZRS'],
    '20': ['PZR', 'PZ', 'P', 'PZRS'],
    '41': ['PZ', 'P', 'PZRS', 'PZR'],
    '44': ['P', 'PZRS', 'PZR', 'PZ'],
    '24': ['PZRS', 'PZR', 'PZ', 'P'],
    '14': ['PZRS', 'PZR', 'PZ', 'P'],
    '75': ['PZR', 'PZ', 'P', 'PZRS'],
    '32': ['PZ', 'P', 'PZRS', 'PZR'],
    '52': ['P', 'PZRS', 'PZR', 'PZ'],
    '30': ['P', 'P', 'P', 'P'],
    '38': ['PZ', 'PZ', 'PZ', 'PZ'],
    '37': ['PZR', 'PZR', 'PZR', 'PZR'],
    '29': ['PZRS', 'PZRS', 'PZRS', 'PZRS']
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
