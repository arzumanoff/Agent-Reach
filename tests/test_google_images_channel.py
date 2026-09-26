import json
from unittest.mock import patch

from agent_reach.channels.google_images import GoogleImagesChannel


class Config:
    def get(self, key, default=None):
        return {"google_api_key": "key", "google_cx": "cx"}.get(key, default)


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n=-1):
        return json.dumps({
            "items": [{
                "title": "PCB",
                "link": "https://images.example/pcb.jpg",
                "mime": "image/jpeg",
                "image": {"contextLink": "https://example/pcb", "width": 1000, "height": 800},
            }]
        }).encode()


def test_google_image_search_returns_structured_results():
    channel = GoogleImagesChannel()
    with patch("agent_reach.channels.google_images.urllib.request.urlopen", return_value=Response()):
        results = channel.search("GPU PCB", Config(), limit=1)
    assert results[0]["title"] == "PCB"
    assert results[0]["width"] == 1000
    assert results[0]["context_url"] == "https://example/pcb"
