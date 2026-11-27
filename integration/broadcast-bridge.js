/* Read existing snapshots only. No fetch, storage, credentials or generation actions. */
export function createDonaBridge(doc) {
  let latest = null, latestAt = 0;
  const dispatch = detail => doc.dispatchEvent(new doc.defaultView.CustomEvent('dona-qv:status', { detail }));
  doc.addEventListener('dona-qv:subscribe', () => {
    if (!latest) return;
    if (['complete', 'failed', 'cancelled'].includes(latest.type) && doc.defaultView.performance.now() - latestAt >= 8000) return;
    try { dispatch(latest); } catch {}
  });
  function emit(run, type, fields = {}) {
    if (!run || !/^[a-f0-9]{32}$/.test(run.trace || '')) return;
    if (run.donaTerminal && type !== 'reset') return;
    if (!run.donaStarted && type !== 'start') emit(run, 'start');
    if (type === 'start') {
      if (run.donaStarted) return;
      run.donaStarted = true;
      run.donaSeq = 0;
    }
    const safe = {};
    for (const key of ['http', 'attempt', 'maxAttempts', 'retryCount', 'retryMax', 'retryRemainingMs', 'inputTokens', 'thinkingTokens', 'outputTokens', 'thinkingAndOutputTokens', 'totalTokens']) {
      if (Number.isSafeInteger(fields[key]) && fields[key] >= 0 && fields[key] <= 1000000000) safe[key] = fields[key];
    }
    if (typeof fields.transferSeconds === 'number' && Number.isFinite(fields.transferSeconds) && fields.transferSeconds >= 0 && fields.transferSeconds <= 86400) safe.transferSeconds = fields.transferSeconds;
    if (['http', 'network', 'timeout', 'invalid_response', 'unknown'].includes(fields.reason)) safe.reason = fields.reason;
    const key = JSON.stringify([type, safe]);
    if (run.donaLast === key) return;
    run.donaLast = key;
    run.donaTerminal = ['complete', 'failed', 'cancelled', 'reset'].includes(type);
    try {
      latest = { version: 1, runId: run.trace, seq: run.donaSeq++, type, ...safe };
      latestAt = doc.defaultView.performance.now();
      dispatch(latest);
    } catch { /* Display failures cannot affect the original request. */ }
  }
  function update(run, snapshot) {
    if (!snapshot) return;
    const last = snapshot.attempts?.at(-1) || snapshot.host_error || {};
    const data = { ...snapshot.dona, http: last.code, reason: last.reason,
      attempt: snapshot.dona?.attempt ?? last.attempt, retryRemainingMs: snapshot.retry_remaining_ms };
    const phase = snapshot.phase;
    if (phase === 'retry_wait') emit(run, 'retry', data);
    else if (phase === 'running') emit(run, snapshot.dona?.streaming ? 'streaming' : snapshot.attempts?.length ? 'connecting' : 'waiting', data);
    else if (phase === 'finished') emit(run, 'complete', data);
    else if (phase === 'failed' || phase === 'cancelled') emit(run, phase, data);
  }
  return { emit, update };
}
