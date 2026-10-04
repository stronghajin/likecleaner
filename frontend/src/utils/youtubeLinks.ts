// YouTube addresses, built in one place (DECISIONS.md 60). Plain links: no API call, no quota.

export const videoUrl = (videoId: string) => `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}`

export const playlistUrl = (playlistId: string) =>
  `https://www.youtube.com/playlist?list=${encodeURIComponent(playlistId)}`
