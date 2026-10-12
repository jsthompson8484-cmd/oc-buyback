# ocbuyback.com DNS snapshot — before Netlify cutover (Oct 12, 2026)

Captured live. Keep this: it is the rollback reference and the rebuild list
if the domain ever moves to a different DNS host.

## Records that MUST be preserved (Google Workspace email + verification)

| Type | Name | Priority | Value |
|---|---|---|---|
| MX | @ | 1  | aspmx.l.google.com. |
| MX | @ | 5  | alt1.aspmx.l.google.com. |
| MX | @ | 5  | alt2.aspmx.l.google.com. |
| MX | @ | 10 | aspmx2.googlemail.com. |
| MX | @ | 10 | aspmx3.googlemail.com. |
| TXT | @ | — | v=spf1 include:_spf.google.com ~all |
| TXT | @ | — | google-site-verification=2WVmmRnb5A1TBUAekUIBw8_FCgEEA-aJ59bTRxNE6sc |

No DKIM (google._domainkey) or DMARC record exists today.

## GoDaddy service records (leave alone unless retiring the service)

| Type | Name | Value | Note |
|---|---|---|---|
| CNAME | pay | paylinks.commerce.godaddy.com. | GoDaddy payment links |
| CNAME | _domainconnect | _domainconnect.gd.domaincontrol.com. | Domain Connect — this is what LOCKS the A records |

## The records being changed at cutover (currently FlipTech/Heroku)

| Type | Name | OLD value (rollback to this) | NEW value (Netlify) |
|---|---|---|---|
| A | @ | 15.197.225.128 | 75.2.60.5 |
| A | @ | 3.33.251.168 | (delete — keep a single A record) |
| CNAME | www | www.ocbuyback.com.herokudns.com. | ocbuyback.netlify.app |

Nameservers today: ns03.domaincontrol.com / ns04.domaincontrol.com (GoDaddy).
