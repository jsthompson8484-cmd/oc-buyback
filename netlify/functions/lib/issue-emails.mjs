// Issue email templates. Inline-styled HTML for email-client compatibility,
// Fresh Air palette. Every template gets tokenized action links whose click
// resolves the issue (see issue-respond.mjs).
//
// Copy rules: no insurance mentions, no marketplace language, no PayPal.

const GREEN = "#2D8631", DEEP = "#1E6323", GROUND = "#f5f8f4", MUTED = "#5c6e64", LINE = "#e3eae2";

const money = (v) => "$" + Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function button(href, label, solid = true) {
  const style = solid
    ? `background:${GREEN};color:#ffffff;border:2px solid ${GREEN};`
    : `background:#ffffff;color:${DEEP};border:2px solid ${LINE};`;
  return `<a href="${href}" style="${style}display:inline-block;padding:13px 26px;border-radius:99px;
    font-weight:700;font-size:15px;text-decoration:none;margin:6px 6px 0 0">${label}</a>`;
}

function layout({ heading, intro, bodyHtml, buttonsHtml, footNote, orderNumber }) {
  return `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:${GROUND}">
  <div style="max-width:560px;margin:0 auto;padding:28px 16px;font-family:Helvetica,Arial,sans-serif;color:#182420">
    <div style="font-size:20px;font-weight:800;color:${DEEP};padding:6px 0 18px">
      OC<span style="color:${GREEN}">BuyBack</span></div>
    <div style="background:#ffffff;border:1px solid ${LINE};border-radius:16px;padding:28px">
      <div style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:${MUTED};font-weight:700">
        Order ${esc(orderNumber)}</div>
      <h1 style="font-size:22px;line-height:1.25;color:${DEEP};margin:8px 0 12px">${heading}</h1>
      <p style="font-size:15px;line-height:1.6;margin:0 0 16px">${intro}</p>
      ${bodyHtml || ""}
      <div style="margin-top:20px">${buttonsHtml}</div>
      ${footNote ? `<p style="font-size:13px;color:${MUTED};line-height:1.55;margin:18px 0 0">${footNote}</p>` : ""}
    </div>
    <p style="font-size:12.5px;color:${MUTED};text-align:center;margin:18px 0 0">
      OCBuyBack · 1203 W Imperial Hwy, STE 103, Brea, CA 92821 · 657-286-8274<br>
      Questions? Just reply to this email.</p>
  </div></body></html>`;
}

const steps = (items) =>
  `<ol style="font-size:14.5px;line-height:1.7;margin:0 0 4px;padding-left:20px">` +
  items.map((s) => `<li style="margin-bottom:6px">${s}</li>`).join("") + `</ol>`;

function priceBox({ device, oldLabel, oldPrice, newLabel, newPrice }) {
  return `<div style="background:${GROUND};border-radius:12px;padding:16px 18px;margin:14px 0">
    <div style="font-weight:700;font-size:15px;margin-bottom:8px">${esc(device)}</div>
    <table style="width:100%;font-size:14.5px;border-collapse:collapse">
      <tr><td style="color:${MUTED};padding:3px 0">Original quote — ${esc(oldLabel)}</td>
          <td style="text-align:right;color:${MUTED};text-decoration:line-through">${money(oldPrice)}</td></tr>
      <tr><td style="font-weight:700;padding:3px 0">Revised offer — ${esc(newLabel)}</td>
          <td style="text-align:right;font-weight:800;color:${GREEN};font-size:18px">${money(newPrice)}</td></tr>
    </table></div>`;
}

/**
 * Build subject + html for an issue email.
 * issue: {type, message, new_condition, new_price}
 * ctx: {orderNumber, firstName, device, condition, quotedPrice, respondUrl}
 *   respondUrl(action) -> full URL for that action link
 */
export function buildIssueEmail(issue, ctx) {
  const { orderNumber, firstName, device, respondUrl } = ctx;
  const note = issue.message
    ? `<p style="font-size:14.5px;line-height:1.6;background:${GROUND};border-radius:12px;padding:12px 16px;margin:0 0 14px"><b>Note from our team:</b> ${esc(issue.message)}</p>`
    : "";

  switch (issue.type) {
    case "icloud_lock":
      return {
        subject: `Action needed on order ${orderNumber} — remove iCloud lock`,
        html: layout({
          orderNumber,
          heading: "Your device still has Find My iPhone turned on",
          intro: `Hi ${esc(firstName)} — your <b>${esc(device)}</b> arrived, but it's still linked to an iCloud account, which blocks us from completing your trade-in. It takes about a minute to remove remotely:`,
          bodyHtml: note + steps([
            `Go to <a href="https://icloud.com/find" style="color:${GREEN}">icloud.com/find</a> and sign in with your Apple ID`,
            `Select <b>All Devices</b> and choose your ${esc(device)}`,
            `Click <b>Remove from Account</b> (if asked, choose Erase first, then Remove)`,
          ]),
          buttonsHtml: button(respondUrl("done"), "I've removed it ✓") +
                       button(respondUrl("cannot"), "I'm not able to", false),
        }),
      };

    case "google_lock":
      return {
        subject: `Action needed on order ${orderNumber} — remove Google account lock`,
        html: layout({
          orderNumber,
          heading: "Your device is still locked to a Google account",
          intro: `Hi ${esc(firstName)} — your <b>${esc(device)}</b> arrived, but it still has a Google account attached (factory reset protection). Here's how to remove it from any browser:`,
          bodyHtml: note + steps([
            `Go to <a href="https://myaccount.google.com/device-activity" style="color:${GREEN}">myaccount.google.com/device-activity</a> and sign in`,
            `Find your ${esc(device)} in the list`,
            `Click it, then choose <b>Sign out</b>`,
          ]),
          buttonsHtml: button(respondUrl("done"), "I've removed it ✓") +
                       button(respondUrl("cannot"), "I'm not able to", false),
        }),
      };

    case "financing":
      return {
        subject: `Action needed on order ${orderNumber} — carrier balance on your device`,
        html: layout({
          orderNumber,
          heading: "Your device still has a balance with your carrier",
          intro: `Hi ${esc(firstName)} — your <b>${esc(device)}</b> arrived, but our check shows it isn't fully paid off with the carrier, so it can't be activated by a new owner yet. To finish your trade-in:`,
          bodyHtml: note + steps([
            `Contact your carrier and pay off the remaining installment balance on this device`,
            `Ask them to confirm the device is <b>paid off and unlocked</b>`,
            `Come back and confirm below — we'll re-check it on our end`,
          ]),
          buttonsHtml: button(respondUrl("done"), "It's paid off now ✓") +
                       button(respondUrl("cannot"), "I'm not able to", false),
        }),
      };

    case "requote":
      return {
        subject: `Revised offer for order ${orderNumber} — ${money(issue.new_price)}`,
        html: layout({
          orderNumber,
          heading: "We've re-graded your device",
          intro: `Hi ${esc(firstName)} — after inspecting your <b>${esc(device)}</b>, its condition came in as <b>${esc(issue.new_condition)}</b> rather than ${esc(ctx.condition)}. Here's the updated offer:`,
          bodyHtml: note + priceBox({
            device, oldLabel: ctx.condition, oldPrice: ctx.quotedPrice,
            newLabel: issue.new_condition, newPrice: issue.new_price,
          }),
          buttonsHtml: button(respondUrl("accept"), `Accept ${money(issue.new_price)} ✓`) +
                       button(respondUrl("decline"), "Decline — return my device", false),
          footNote: "Accept and you'll be paid within 1 business day. Decline and we'll ship your device back free — no hard feelings either way.",
        }),
      };

    default: // 'other' — admin writes the issue; revised price optional
      return {
        subject: issue.new_price != null
          ? `Revised offer for order ${orderNumber} — ${money(issue.new_price)}`
          : `About your trade-in — order ${orderNumber}`,
        html: layout({
          orderNumber,
          heading: "An update on your device",
          intro: `Hi ${esc(firstName)} — while processing your <b>${esc(device)}</b> we ran into something that needs your OK:`,
          bodyHtml:
            `<p style="font-size:15px;line-height:1.6;background:${GROUND};border-radius:12px;padding:14px 16px;margin:0 0 14px">${esc(issue.message || "")}</p>` +
            (issue.new_price != null
              ? priceBox({ device, oldLabel: "as quoted", oldPrice: ctx.quotedPrice,
                           newLabel: "revised offer", newPrice: issue.new_price })
              : ""),
          buttonsHtml: issue.new_price != null
            ? button(respondUrl("accept"), `Accept ${money(issue.new_price)} ✓`) +
              button(respondUrl("decline"), "Decline — return my device", false)
            : button(respondUrl("done"), "Sounds good ✓") +
              button(respondUrl("cannot"), "I have a question", false),
          footNote: "Accept and you'll be paid within 1 business day. Decline and we'll ship your device back free.",
        }),
      };
  }
}

// "Get your device ready" checklists, keyed by what's in the order.
const RESET_GUIDES = [
  { match: (i) => i.brand === "Apple" && ["Cell Phone","Tablet","iPod","VR"].includes(i.cat || i.category),
    title: "iPhone / iPad",
    steps: ["Back up anything you want to keep (iCloud or computer).",
      "Turn off Find My and sign out: Settings → your name → Sign Out.",
      "Erase it: Settings → General → Transfer or Reset → Erase All Content and Settings.",
      "Remove your SIM card if it has one."] },
  { match: (i) => i.brand === "Apple" && (i.cat || i.category) === "Smartwatch",
    title: "Apple Watch",
    steps: ["On your iPhone, open the Watch app → All Watches → tap ⓘ → Unpair Apple Watch.",
      "Unpairing automatically removes Activation Lock — no other steps needed."] },
  { match: (i) => i.brand !== "Apple" && ["Cell Phone","Tablet"].includes(i.cat || i.category),
    title: "Android phone / tablet",
    steps: ["Back up anything you want to keep.",
      "Remove your Google account: Settings → Accounts (or Passwords & accounts) → remove.",
      "Remove any screen lock, then factory reset: Settings → General management (or System) → Reset.",
      "Remove your SIM card if it has one."] },
  { match: (i) => (i.cat || i.category) === "Game Console",
    title: "Game console",
    steps: ["Sign out / deactivate your accounts (PlayStation: Settings → Users and Accounts; Xbox: remove account; Nintendo: deregister).",
      "Factory reset from system settings.",
      "Include the power cable, and controllers if you have them."] },
  { match: (i) => (i.cat || i.category) === "GoPro",
    title: "GoPro",
    steps: ["Take out your SD card — we don't need it and can't return it.",
      "Factory reset: Preferences → Reset → Factory Reset."] },
  { match: (i) => (i.cat || i.category) === "Headphones",
    title: "Headphones",
    steps: ["Remove them from Find My / Bluetooth on your devices so they're fully unpaired."] },
];

// Order confirmation sent right after checkout.
export function buildOrderConfirmation({ orderNumber, firstName, items, total, lockedUntil, payMethod, trackUrl, labelUrl, qrUrl, tracking, shipCarrier = "USPS" }) {
  const isCash = payMethod === "cash";
  const rows = items.map((i) =>
    `<tr><td style="padding:4px 0;font-size:14.5px">${esc(i.brand)} ${esc(i.device || i.model)} × ${i.qty}
       <span style="color:${MUTED}">· ${esc(i.cond)}</span></td>
     <td style="text-align:right;font-weight:700">${money(i.price * i.qty)}</td></tr>`).join("");
  return {
    subject: `Order ${orderNumber} confirmed — ${money(total)} locked in`,
    html: layout({
      orderNumber,
      heading: isCash ? "You're all set — see you at the shop!" : "You're all set — here's what happens next",
      intro: `Hi ${esc(firstName)} — your trade-in is confirmed and your price is locked through <b>${lockedUntil}</b>.`,
      bodyHtml: `<div style="background:${GROUND};border-radius:12px;padding:14px 18px;margin:0 0 16px">
        <table style="width:100%;border-collapse:collapse">${rows}
        <tr><td style="padding:8px 0 0;font-weight:800">Total offer</td>
        <td style="text-align:right;font-weight:800;color:${GREEN};font-size:18px;padding-top:8px">${money(total)}</td></tr></table></div>` +
        (isCash
          ? `<h3 style="font-size:16px;color:${DEEP};margin:20px 0 8px">🏪 Come get paid</h3>
             <div style="background:${GROUND};border-radius:12px;padding:16px 18px;margin:0 0 12px">
               <p style="font-size:14.5px;line-height:1.7;margin:0"><b>OCBuyBack</b><br>
               1203 W Imperial Hwy, STE 103<br>Brea, CA 92821<br>
               <span style="color:${MUTED}">Monday–Friday · 10 AM – 6 PM · no appointment needed</span></p>
             </div>
             <p style="font-size:14.5px;line-height:1.6;margin:0 0 6px">Show your order number <b>${orderNumber}</b> at the counter — your price is locked, so what you see above is what we pay. We evaluate while you wait (about 10 minutes) and hand you cash on the spot.</p>
             <p style="font-size:13.5px;color:${MUTED};line-height:1.6;margin:0"><b>Bring:</b> your device, a photo ID, and sign out of iCloud or your Google account first — or ask us and we'll help at the counter.</p>`
          : (qrUrl || labelUrl
            ? `<h3 style="font-size:16px;color:${DEEP};margin:20px 0 8px">📦 Your free ${esc(shipCarrier)} shipping label</h3>` +
              (qrUrl ? `<div style="background:${GROUND};border-radius:12px;padding:16px;text-align:center;margin:0 0 10px">
                 <img src="${qrUrl}" alt="USPS QR code" style="width:180px;max-width:60%">
                 <p style="font-size:13.5px;color:${MUTED};margin:8px 0 0"><b>No printer needed:</b> show this QR code at any Post Office and they'll print the label for you.</p></div>` : "") +
              (labelUrl ? `<p style="font-size:14px;margin:0 0 6px">Have a printer? <a href="${labelUrl}" style="color:${GREEN};font-weight:700">Print your shipping label here</a>.</p>` : "") +
              (tracking ? `<p style="font-size:13px;color:${MUTED};margin:0 0 4px">Tracking number: <b>${esc(tracking)}</b></p>` : "") +
              (shipCarrier === "USPS"
                ? `<p style="font-size:13px;color:${MUTED};margin:0">This label carries the required lithium-battery (HAZMAT Class 9) marking — ground shipping only, which USPS handles automatically.</p>`
                : `<p style="font-size:13px;color:${MUTED};margin:0">Print the label, tape it to any sturdy box, and drop it off at ${shipCarrier === "FedEx" ? "any FedEx Office or FedEx drop-off location" : "any The UPS Store or UPS drop-off location"}.</p>`)
            : `<p style="font-size:14.5px;line-height:1.6">Your free prepaid USPS shipping label arrives in a separate email shortly.</p>`)),
      buttonsHtml:
        (!isCash ? (() => {
          const guides = RESET_GUIDES.filter((g) => items.some(g.match));
          return guides.length ? `<h3 style="font-size:16px;color:${DEEP};margin:20px 0 8px">🔒 Get your device ready</h3>` +
            guides.map((g) => `<p style="font-size:14px;font-weight:700;margin:10px 0 4px">${g.title}</p>
              <ol style="font-size:13.5px;color:${MUTED};line-height:1.6;margin:0;padding-left:20px">${g.steps.map((s) => `<li>${s}</li>`).join("")}</ol>`).join("") +
            `<div style="margin-top:18px"></div>` : "";
        })() : "") +
        (isCash
          ? button("https://www.google.com/maps/dir/?api=1&destination=OCBuyBack+1203+W+Imperial+Hwy+STE+103+Brea+CA+92821", "Get driving directions")
          : button(trackUrl, "Track my order")),
      footNote: "Questions? Just reply to this email or call 657-286-8274.",
    }),
  };
}

// Friendly page shown in the browser after the customer clicks an email link.
export function responsePage({ title, body }) {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex"><title>${esc(title)} — OCBuyBack</title></head>
  <body style="margin:0;background:${GROUND};font-family:Helvetica,Arial,sans-serif;color:#182420">
  <div style="max-width:480px;margin:14vh auto 0;padding:0 18px;text-align:center">
    <div style="font-size:22px;font-weight:800;color:${DEEP};margin-bottom:20px">OC<span style="color:${GREEN}">BuyBack</span></div>
    <div style="background:#fff;border:1px solid ${LINE};border-radius:16px;padding:34px 28px">
      <h1 style="font-size:22px;color:${DEEP};margin:0 0 10px">${esc(title)}</h1>
      <p style="font-size:15px;line-height:1.6;color:${MUTED};margin:0">${body}</p>
    </div>
    <p style="font-size:12.5px;color:${MUTED};margin-top:16px">Questions? Call 657-286-8274 or reply to our email.</p>
  </div></body></html>`;
}
