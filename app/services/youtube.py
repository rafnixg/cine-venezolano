from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

API_ROOT = "https://www.googleapis.com/youtube/v3"


class YouTubeSyncError(RuntimeError):
    pass


@dataclass
class YouTubeItem:
    video_id: str
    position: int
    playlist_added_at: str | None
    playlist_title: str
    playlist_description: str
    video: dict[str, Any] | None


class YouTubeClient:
    def __init__(
        self,
        api_key: str,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise YouTubeSyncError("YOUTUBE_API_KEY no está configurada")
        self.api_key = api_key
        self.client = client or httpx.Client(timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        self.client.close()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.client.get(f"{API_ROOT}/{path}", params={**params, "key": self.api_key})
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text[:500]
            raise YouTubeSyncError(f"YouTube respondió {response.status_code}: {detail}") from exc
        return response.json()

    def fetch_playlist(self, playlist_id: str) -> list[YouTubeItem]:
        playlist_items: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {
                "part": "snippet,contentDetails,status",
                "playlistId": playlist_id,
                "maxResults": 50,
            }
            if page_token:
                params["pageToken"] = page_token
            page = self._get("playlistItems", params)
            playlist_items.extend(page.get("items", []))
            page_token = page.get("nextPageToken")
            if not page_token:
                break

        video_ids = [
            item.get("contentDetails", {}).get("videoId")
            or item.get("snippet", {}).get("resourceId", {}).get("videoId")
            for item in playlist_items
        ]
        valid_ids = [video_id for video_id in video_ids if video_id]
        videos: dict[str, dict[str, Any]] = {}
        for start in range(0, len(valid_ids), 50):
            batch = valid_ids[start : start + 50]
            page = self._get(
                "videos",
                {
                    "part": "snippet,contentDetails,status,statistics",
                    "id": ",".join(batch),
                    "maxResults": 50,
                },
            )
            videos.update({video["id"]: video for video in page.get("items", [])})

        result: list[YouTubeItem] = []
        for item in playlist_items:
            snippet = item.get("snippet", {})
            video_id = item.get("contentDetails", {}).get("videoId") or snippet.get(
                "resourceId", {}
            ).get("videoId")
            if not video_id:
                continue
            result.append(
                YouTubeItem(
                    video_id=video_id,
                    position=int(snippet.get("position", 0)),
                    playlist_added_at=snippet.get("publishedAt"),
                    playlist_title=snippet.get("title") or video_id,
                    playlist_description=snippet.get("description") or "",
                    video=videos.get(video_id),
                )
            )
        return result


def best_thumbnail(snippet: dict[str, Any], video_id: str) -> str:
    thumbnails = snippet.get("thumbnails", {})
    for size in ("maxres", "standard", "high", "medium", "default"):
        if thumbnails.get(size, {}).get("url"):
            return thumbnails[size]["url"]
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
