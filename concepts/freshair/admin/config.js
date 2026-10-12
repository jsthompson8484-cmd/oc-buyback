// Fill these in after creating the Supabase project (Settings → API).
// The anon key is safe to ship client-side — RLS restricts writes to the
// admin allowlist in is_admin() (supabase/schema.sql).
window.OCB_CONFIG = {
  SUPABASE_URL: "https://bpvlohcbdhvttocsijrm.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwdmxvaGNiZGh2dHRvY3NpanJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg4ODg1NTUsImV4cCI6MjEwNDQ2NDU1NX0.ErvyjDmG3LMgNnCSQt_u9cBk4CAdE19OLHZJga2O7d8",
  ADMIN_EMAILS: ["js@neartechpartners.com", "henry@ocbuyback.com"], // keep in sync with is_admin() in schema.sql
};
