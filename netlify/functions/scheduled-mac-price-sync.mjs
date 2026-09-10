// Daily Mac price-feed sync — 13:00 UTC = 6:00 AM Pacific (during PDT),
// matching the feed provider's "refreshed by 6 AM Pacific" contract.
//
// Scheduled functions arrive as plain POSTs with no auth — do NOT 401 them.
// Worst case an outsider triggers an early sync of the same public feed data;
// the RPC's guards make that harmless.

import { runMacPriceSync } from "./lib/mac-price-sync.mjs";

export default async () => {
  const result = await runMacPriceSync("scheduled");
  console.log("mac price sync:", JSON.stringify(result));
  return new Response(JSON.stringify(result), {
    status: result.error ? 502 : 200,
    headers: { "content-type": "application/json" },
  });
};

export const config = { schedule: "0 13 * * *" };
