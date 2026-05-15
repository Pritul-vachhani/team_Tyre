// Tire brand specs: estimated tread life (miles) and new tread depth (mm)
export const TIRE_BRANDS = {
  "Michelin Pilot Sport 4S":           { treadLife: 30000, treadDepth: 10.5 },
  "Bridgestone Potenza Sport":          { treadLife: 25000, treadDepth: 10.0 },
  "Continental ExtremeContact DWS06+":  { treadLife: 50000, treadDepth: 10.0 },
  "Goodyear Eagle F1 Asymmetric 6":     { treadLife: 40000, treadDepth: 9.5  },
  "Pirelli P Zero":                     { treadLife: 30000, treadDepth: 9.5  },
  "Yokohama Advan Sport V107":          { treadLife: 35000, treadDepth: 10.0 },
  "Hankook Ventus S1 evo3":             { treadLife: 45000, treadDepth: 9.5  },
  "Toyo Proxes Sport":                  { treadLife: 40000, treadDepth: 10.0 },
  "Dunlop Sport Maxx RT2":              { treadLife: 30000, treadDepth: 9.5  },
  "BFGoodrich g-Force COMP-2 A/S+":    { treadLife: 45000, treadDepth: 10.0 },
  "Generic / Unknown Brand":            { treadLife: 40000, treadDepth: 9.5  },
}

// Safety thresholds (mm)
export const TREAD_LEGAL_MIN  = 1.6  // legal minimum in most US states
export const TREAD_SAFETY_MIN = 3.0  // recommended replacement threshold
export const TREAD_USABLE_MIN = 2.0  // used for RUL calculation

// Age threshold (years) after which age-based inspection warning fires
export const AGE_WARNING_YEARS = 6
