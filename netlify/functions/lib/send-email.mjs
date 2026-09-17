// One sendEmail() for every function. Provider by env:
//   SENDGRID_API_KEY set  -> SendGrid (interim: the grandfathered FlipTech
//     account sends as support@ocbuyback.com today, but it is NOT Henry's
//     account and ocbuyback.com is not domain-authenticated there — treat as
//     a bridge until the domain is verified in Resend)
//   otherwise             -> Resend (RESEND_API_KEY; sandbox only delivers to
//     the account owner until ocbuyback.com is verified)
// Returns { ok, detail } — callers decide how loudly to fail.

const SENDGRID_KEY = process.env.SENDGRID_API_KEY;
const RESEND_KEY = process.env.RESEND_API_KEY;

const SG_FROM = process.env.EMAIL_FROM_ADDRESS || "support@ocbuyback.com";
const RESEND_FROM = process.env.EMAIL_FROM || "OCBuyBack <onboarding@resend.dev>";

export const emailConfigured = () => Boolean(SENDGRID_KEY || RESEND_KEY);

export async function sendEmail({ to, subject, html, replyTo = "support@ocbuyback.com" }) {
  if (SENDGRID_KEY) {
    const r = await fetch("https://api.sendgrid.com/v3/mail/send", {
      method: "POST",
      headers: { authorization: `Bearer ${SENDGRID_KEY}`, "content-type": "application/json" },
      body: JSON.stringify({
        personalizations: [{ to: [{ email: to }] }],
        from: { email: SG_FROM, name: "OCBuyBack" },
        reply_to: { email: replyTo },
        subject,
        content: [{ type: "text/html", value: html }],
      }),
    });
    return { ok: r.ok, detail: r.ok ? "sendgrid" : `sendgrid ${r.status}: ${(await r.text()).slice(0, 200)}` };
  }
  if (RESEND_KEY) {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: `Bearer ${RESEND_KEY}`, "content-type": "application/json" },
      body: JSON.stringify({ from: RESEND_FROM, to, subject, html, reply_to: replyTo }),
    });
    return { ok: r.ok, detail: r.ok ? "resend" : `resend ${r.status}: ${(await r.text()).slice(0, 200)}` };
  }
  return { ok: false, detail: "no email provider configured" };
}
