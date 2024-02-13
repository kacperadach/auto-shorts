import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  "https://xlgxdmsfathlpknedcfz.supabase.co",
  process.env.REACT_APP_ANON_KEY as string
);
