import httpx
import pytest

from app.services.youtube import YouTubeClient, YouTubeSyncError


def playlist_entry(index: int) -> dict:
    video_id = f"video{index:06d}"
    return {
        "snippet": {
            "position": index,
            "publishedAt": "2025-01-01T00:00:00Z",
            "title": f"Obra {index}",
            "resourceId": {"videoId": video_id},
        },
        "contentDetails": {"videoId": video_id},
    }


def test_playlist_pagination_and_video_batching() -> None:
    playlist_calls = 0
    video_batch_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal playlist_calls
        if request.url.path.endswith("/playlistItems"):
            playlist_calls += 1
            start = 0 if playlist_calls == 1 else 50
            count = 50 if playlist_calls == 1 else 1
            body = {"items": [playlist_entry(i) for i in range(start, start + count)]}
            if playlist_calls == 1:
                body["nextPageToken"] = "next"
            return httpx.Response(200, json=body)
        ids = request.url.params["id"].split(",")
        video_batch_sizes.append(len(ids))
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": video_id,
                        "snippet": {"title": video_id},
                        "contentDetails": {"duration": "PT10M"},
                        "status": {"privacyStatus": "public"},
                    }
                    for video_id in ids
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = YouTubeClient("test-key", client=http_client)
    try:
        items = client.fetch_playlist("playlist")
    finally:
        client.close()

    assert len(items) == 51
    assert playlist_calls == 2
    assert video_batch_sizes == [50, 1]


def test_api_error_is_reported_without_exposing_key() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "quota exceeded"}})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = YouTubeClient("secret-key", client=http_client)
    with pytest.raises(YouTubeSyncError, match="403") as error:
        client.fetch_playlist("playlist")
    assert "secret-key" not in str(error.value)
    client.close()
