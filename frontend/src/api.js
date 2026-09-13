// Thin fetch helpers over the Flask JSON API. Every handler raises on
// non-2xx so callers can rely on try/catch.

export async function getJSON(url) {
  const resp = await fetch(url);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Request failed (${resp.status})`);
  return data;
}

export async function postJSON(url, body = {}) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Request failed (${resp.status})`);
  return data;
}

export async function uploadFiles(files) {
  const form = new FormData();
  Array.from(files || []).forEach((f) => form.append("files", f));
  const resp = await fetch("/api/ingest", { method: "POST", body: form });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Upload failed (${resp.status})`);
  return data;
}
