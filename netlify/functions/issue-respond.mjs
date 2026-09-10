// /api/issue-respond?token=...&action=... — the customer clicked a link
// in an issue email.
//
// GET shows a confirmation page with a button; only the button's POST records
// the response. Email security scanners (Outlook SafeLinks, AV gateways)
// prefetch every link with GET — if GET mutated, an offer could be accepted
// or declined before the customer ever opened the email.
// The recording PATCH is conditional on status=eq.pending, so concurrent
// clicks record exactly once.

import { responsePage } from "./lib/issue-emails.mjs";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const db = (path, init = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json", prefer: "return=representation", ...init.headers },
  });

const html = (status, page) =>
  new Response(page, { status, headers: { "content-type": "text/html; charset=utf-8" } });

// action -> resulting issue status
const ACTIONS = { done: "resolved", cannot: "cannot_complete", accept: "accepted", decline: "declined" };

export default async (req) => {
  const url = new URL(req.url);
  const token = url.searchParams.get("token") || "";
  const action = url.searchParams.get("action") || "";
  const newStatus = ACTIONS[action];

  if (!token || !newStatus)
    return html(400, responsePage({ title: "That link doesn't look right",
      body: "Please use the buttons in the email we sent you, or reply to the email and we'll sort it out." }));

  const [issue] = await db(
    `trade_in_issues?token=eq.${encodeURIComponent(token)}&select=*,` +
    `trade_ins(id,order_number,first_name,status),trade_in_items:item_id(id,brand,model,qty)`
  ).then((r) => r.json());

  if (!issue)
    return html(404, responsePage({ title: "Link not found",
      body: "This link may have been replaced by a newer email about your order. Check your inbox for our latest message, or reply and we'll help." }));

  const device = issue.trade_in_items ? `${issue.trade_in_items.brand} ${issue.trade_in_items.model}` : "your device";
  const first = issue.trade_ins.first_name;

  // already answered → show what we have on file, don't double-record
  const alreadyPage = () => {
    const already = {
      resolved: "You've already confirmed this is done — we're on it.",
      cannot_complete: "You've already let us know you couldn't complete this — we're arranging the return.",
      accepted: "You've already accepted the revised offer — payment is on its way.",
      declined: "You've already declined the revised offer — your device is being returned.",
      cancelled: "This issue was withdrawn by our team — no action needed.",
    }[issue.status] || "This has already been handled — reply to our email if anything looks off.";
    return html(200, responsePage({ title: "Already taken care of", body: already }));
  };
  if (issue.status !== "pending") return alreadyPage();

  // GET = show the confirm button; only its POST records the choice
  if (req.method !== "POST") {
    const label = {
      done: "Yes — I've completed this",
      cannot: "I wasn't able to complete this",
      accept: `Accept the revised offer${issue.new_price ? ` of $${Number(issue.new_price).toLocaleString()}` : ""}`,
      decline: "Decline — send my device back",
    }[action];
    const qs = `token=${encodeURIComponent(token)}&action=${encodeURIComponent(action)}`;
    return html(200, responsePage({
      title: `One tap to confirm, ${first}`,
      body: `This will record your choice for ${device} on order <b>${issue.trade_ins.order_number}</b>.` +
        `<form method="POST" action="/api/issue-respond?${qs}" style="margin:22px 0 0">` +
        `<button type="submit" style="background:#2D8631;color:#fff;border:0;border-radius:10px;` +
        `padding:14px 26px;font-size:15px;font-weight:700;cursor:pointer">${label}</button></form>` +
        `<span style="display:block;margin-top:14px;font-size:13px">Changed your mind? Just close this page ` +
        `and use the other button in our email.</span>`,
    }));
  }

  // claim: only records while still pending — first response wins
  const claim = await db(`trade_in_issues?id=eq.${issue.id}&status=eq.pending`, {
    method: "PATCH",
    body: JSON.stringify({ status: newStatus, responded_at: new Date().toISOString() }),
  });
  const claimed = claim.ok ? await claim.json() : [];
  if (!claimed.length) {
    const [cur] = await db(`trade_in_issues?id=eq.${issue.id}&select=status`).then((r) => r.json());
    issue.status = cur?.status || issue.status;
    return alreadyPage();
  }

  let note, page;
  switch (newStatus) {
    case "resolved":
      note = `Customer confirmed completed: ${issue.type.replace("_", " ")} on ${device}`;
      if (issue.trade_ins.status === "action_pending")
        await db(`trade_ins?id=eq.${issue.trade_ins.id}`, { method: "PATCH", body: JSON.stringify({ status: "evaluating" }) });
      page = { title: `Thanks, ${first}!`,
        body: `We'll verify ${device} and finish your evaluation the same business day. You'll get a confirmation email once it's done.` };
      break;
    case "cannot_complete":
      note = `Customer can't complete: ${issue.type.replace("_", " ")} on ${device} — arrange return or follow up`;
      page = { title: "No problem — we've got it from here",
        body: `We've noted that you weren't able to complete this. Our team will follow up by email — usually to arrange a free return of ${device}, or to help another way.` };
      break;
    case "accepted": {
      note = `Customer ACCEPTED revised offer of $${issue.new_price} for ${device}`;
      if (issue.item_id)
        await db(`trade_in_items?id=eq.${issue.item_id}`, {
          method: "PATCH",
          body: JSON.stringify({ final_price: issue.new_price,
            final_condition: issue.new_condition || undefined }),
        });
      page = { title: `Deal — $${Number(issue.new_price).toLocaleString()} it is!`,
        body: `You'll be paid within 1 business day. Thanks for trading in with us, ${first}.` };
      break;
    }
    case "declined":
      note = `Customer DECLINED revised offer of $${issue.new_price} for ${device} — ship it back free`;
      page = { title: "Understood — your device is coming back",
        body: `We'll ship ${device} back to you free of charge and email you the tracking number. No hard feelings — we're here if you change your mind.` };
      break;
  }

  await db("trade_in_events", {
    method: "POST",
    body: JSON.stringify({ trade_in_id: issue.trade_ins.id, status: issue.trade_ins.status, note }),
  });

  return html(200, responsePage(page));
};

export const config = { path: "/api/issue-respond" };
