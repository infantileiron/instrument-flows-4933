/** @typedef {{code: string, name: string, manager: string, purpose: string}} Hall */
/** @typedef {{code: string, name: string, unit: string}} Instrument */
/** @typedef {{halls: Hall[], instruments: Instrument[]}} Catalog */
/** @typedef {{username: string, display_name: string, role: 'analyst'|'reviewer'|'observer'}} User */
/**
 * @typedef {Object} SyncItem
 * @property {number} id
 * @property {number} batch_id
 * @property {number} line_no
 * @property {string} reference
 * @property {'loan'|'reversal'} kind
 * @property {string|null} original_reference
 * @property {string|null} source
 * @property {string|null} destination
 * @property {string|null} instrument
 * @property {number|null} quantity
 * @property {'posted'|'pending_original'|'conflict'} status
 * @property {string} detail
 * @property {number|null} receipt_id
 */
