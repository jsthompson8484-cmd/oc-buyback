// POST /api/publish-site — admin-triggered site rebuild (the "Publish" button).
// Rebuilds pull the latest catalog, prices, blog posts, and condition copy
// from the database, so this is how admin edits reach the live pages.

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || "js@neartechpartners.com")
  .split(",").map((e) => e.trim().toLowerCase());
// Netlify build hook "Admin publish" — knowing it only lets you trigger builds
const BUILD_HOOK = process.env.NETLIFY_BUILD_HOOK ||
  "https://api.netlify.com/build_hooks/6aa2f2b7d4432b4d244d7d56";

const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });
  const userToken = (req.headers.get("authorization") || "").replace(/^Bearer /, "");
  const who = userToken ? await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${userToken}` },
  }).then((r) => (r.ok ? r.json() : null)) : null;
  if (!who?.email || !ADMIN_EMAILS.includes(who.email.toLowerCase()))
    return json(403, { error: "Not an admin" });

  const r = await fetch(BUILD_HOOK, { method: "POST" });
  if (!r.ok) return json(502, { error: "Build hook failed" });
  return json(200, { ok: true });
};

export const config = { path: "/api/publish-site" };
