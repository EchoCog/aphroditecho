// Define global types for the app
interface AppEnv {
  SUPABASE_URL: string;
  SUPABASE_ANON_KEY: string;
}

declare global {
  interface Window {
    ENV: AppEnv;
  }
  
  // Allow ENV to be set on globalThis for server-side rendering
  // eslint-disable-next-line no-var
  var ENV: AppEnv;
}

export {};
