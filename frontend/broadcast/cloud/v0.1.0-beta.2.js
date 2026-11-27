/* dona快V · 战术播报 0.1.0-beta.2; fixed-version, one fetch per script activation. */
(async () => {
  const stop = new AbortController();
  window.addEventListener('pagehide', () => stop.abort(), { once: true });
  let blob;
  try {
    const response = await fetch("https://cdn.jsdelivr.net/gh/3086013261qq-hue/dona-QuickV@v0.1.0-beta.2/frontend/broadcast/dona-broadcast.js", { signal: stop.signal, credentials: 'omit', redirect: 'error' });
    if (!response.ok) throw new Error('脚本下载失败：HTTP ' + response.status);
    const chunks = []; let size = 0;
    const reader = response.body.getReader();
    while (true) {
      const { value: chunk, done } = await reader.read();
      if (done) break;
      size += chunk.length;
      if (size > 11807) throw new Error('脚本大小不符');
      chunks.push(chunk);
    }
    const bytes = new Uint8Array(size); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), n => n.toString(16).padStart(2, '0')).join('');
    if (size !== 11807 || digest !== "6a8ccafc90fe43128a65c3e56eae3a39ae5816cf5512a2e513ec4794086a2d8c") throw new Error('脚本 SHA-256 校验失败');
    if (stop.signal.aborted) return;
    blob = URL.createObjectURL(new Blob([bytes], { type: 'text/javascript' }));
    await import(blob);
  } catch (error) {
    if (!stop.signal.aborted) console.error('[dona快V] ' + error.message);
  } finally { if (blob) URL.revokeObjectURL(blob); }
})();
