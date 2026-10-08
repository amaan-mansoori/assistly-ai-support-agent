const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!configured) {
  throw new Error("Set NEXT_PUBLIC_API_BASE_URL before building the production frontend.");
}

let parsed;
try {
  parsed = new URL(configured);
} catch {
  throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute URL.");
}

const localHost = ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname);
if (parsed.protocol !== "https:" && !(parsed.protocol === "http:" && localHost)) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL must use HTTPS except for local development.");
}
if (parsed.username || parsed.password || parsed.search || parsed.hash) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL must not contain credentials, query, or fragment data.");
}
