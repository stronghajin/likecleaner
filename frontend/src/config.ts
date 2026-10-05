// Fixed links shown on screens. Settings that can change (the admin email) come from the backend
// through services (`api.getAppInfo()`, DECISIONS.md 64).

export const EXTERNAL_LINKS = {
  googleUserDataPolicy: 'https://developers.google.com/terms/api-services-user-data-policy',
  youtubeTerms: 'https://www.youtube.com/t/terms',
  googlePrivacy: 'https://policies.google.com/privacy',
  googlePermissions: 'https://myaccount.google.com/permissions',
} as const
