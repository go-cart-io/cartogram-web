export {}

interface CartogramConfig {
  mode?: string
  maps: MapHandlers
  mapName?: string
  mapTitle?: string
  mapDBKey?: string
  cartoVersions?: any
  cartoColorScheme?: string
  choroVersions?: Array<string>
  choroSpec?: any
  maxCartogram?: number
}

declare global {
  interface Window {
    gtag: (...args: any[]) => void
    CARTOGRAM_CONFIG: CartogramConfig
  }
}
