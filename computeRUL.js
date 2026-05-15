import { TIRE_BRANDS, TREAD_USABLE_MIN, AGE_WARNING_YEARS } from '../constants.js'

/**
 * Compute remaining useful life for a tire.
 *
 * @param {object} params
 * @param {number} params.yearsOwned     - How long the user has had the tires
 * @param {number} params.milesPerDay    - Average miles driven per day
 * @param {string} params.brand          - Tire brand key from TIRE_BRANDS
 * @param {string|number} params.currentTread - Measured tread depth in mm (optional, "" to auto-estimate)
 * @returns {object} RUL result object
 */
export function computeRUL({ yearsOwned, milesPerDay, brand, currentTread }) {
  const spec = TIRE_BRANDS[brand] ?? TIRE_BRANDS['Generic / Unknown Brand']

  // Estimate tread worn so far from usage
  const milesOwned  = yearsOwned * 365 * milesPerDay
  const wearRate    = spec.treadDepth / spec.treadLife  // mm per mile
  const treadUsed   = wearRate * milesOwned

  // Use measured tread if provided, otherwise estimate from wear
  const remainingTread =
    currentTread !== '' && currentTread !== null && !isNaN(currentTread)
      ? parseFloat(currentTread)
      : Math.max(TREAD_USABLE_MIN, spec.treadDepth - treadUsed)

  // Usable tread above safety minimum
  const usableTread    = Math.max(0, remainingTread - TREAD_USABLE_MIN)
  const remainingMiles = wearRate > 0 ? usableTread / wearRate : 0
  const remainingYears = milesPerDay > 0 ? remainingMiles / (milesPerDay * 365) : 0

  // Percentage of usable life remaining
  const pctLeft = Math.max(
    0,
    Math.min(100, (remainingTread - TREAD_USABLE_MIN) / (spec.treadDepth - TREAD_USABLE_MIN) * 100)
  )

  // Status label and color
  let status, color
  if (pctLeft > 60)      { status = 'Good';         color = '#22c55e' }
  else if (pctLeft > 30) { status = 'Fair';          color = '#f59e0b' }
  else if (pctLeft > 10) { status = 'Low';           color = '#ef4444' }
  else                   { status = 'Replace Now';   color = '#dc2626' }

  const ageFactor =
    yearsOwned >= AGE_WARNING_YEARS
      ? `⚠ Tires older than ${AGE_WARNING_YEARS} years should be professionally inspected regardless of tread depth.`
      : null

  return {
    remainingMiles,
    remainingYears,
    remainingTread,
    pctLeft,
    status,
    color,
    spec,
    ageFactor,
  }
}
