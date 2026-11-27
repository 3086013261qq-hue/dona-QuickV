/* Whitelist only. Called after the unchanged upstream failure snapshot validator. */
'use strict';
function fields(raw) {
  const d = raw?.dona;
  if (!d || d.version !== 1) return {};
  const result = { version: 1 };
  for (const key of ['attempt', 'maxAttempts', 'retryCount', 'retryMax', 'inputTokens', 'thinkingTokens', 'outputTokens', 'thinkingAndOutputTokens', 'totalTokens']) {
    if (Number.isSafeInteger(d[key]) && d[key] >= 0 && d[key] <= 1000000000) result[key] = d[key];
  }
  result.streaming = d.streaming === true;
  if (typeof d.transferSeconds === 'number' && Number.isFinite(d.transferSeconds) && d.transferSeconds >= 0 && d.transferSeconds <= 86400) result.transferSeconds = d.transferSeconds;
  return { dona: result };
}
module.exports = { fields };
