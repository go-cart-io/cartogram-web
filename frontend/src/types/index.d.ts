export {}

interface CartogramConfig {
  mode: any
  maps: any
  mapName: string
  mapTitle: string
  mapDBKey: string
  cartoVersions: any
  cartoColorScheme: string
  choroVersions: any
  choroSpec: any
}

declare global {
  interface Window {
    gtag: (...args: any[]) => void
    CARTOGRAM_CONFIG: CartogramConfig
  }
}
