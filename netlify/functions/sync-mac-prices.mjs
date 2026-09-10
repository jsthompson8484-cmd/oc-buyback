// POST /api/sync-mac-prices — admin "Sync now" button for the Mac price feed.
// Fetches the external trade-in price feed and applies it to the catalog
// (Mac categories only; see lib/mac-price-sync.mjs for guards).

import { runMacPriceSync } from "./lib/mac-price-sync.mjs";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || "js@neartechpartners.com")
  .split(",").map((e) => e.trim().toLowerCase());

const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });
  const userToken = (req.headers.get("authorization") || "").replace(/^Bearer /, "");
  if (!userToken) return json(401, { error: "Missing auth token" });
  const who = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${userToken}` },
  }).then((r) => (r.ok ? r.json() : null));
  if (!who?.email || !ADMIN_EMAILS.includes(who.email.toLowerCase()))
    return json(403, { error: "Not an admin" });

  const result = await runMacPriceSync("manual");
  return json(result.error ? 502 : 200, result);
};

export const config = { path: "/api/sync-mac-prices" };
