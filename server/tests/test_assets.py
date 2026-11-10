from app.services.assets import detect_image_mime


def test_magic_bytes_determine_image_type():
    assert detect_image_mime(b"\xff\xd8\xffrest") == "image/jpeg"
    assert detect_image_mime(b"\x89PNG\r\n\x1a\nrest") == "image/png"
    assert detect_image_mime(b"RIFF0000WEBPrest") == "image/webp"
    assert detect_image_mime(b"not an image") is None
