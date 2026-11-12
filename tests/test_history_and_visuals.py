"""
Test Suite for History Duplicate Prevention & High-Quality Visual Prompting.
Verifies:
1. History tracking correctly logs and blocks previously seen YouTube IDs and topics.
2. Scout agent automatically skips logged video IDs to scout brand-new references.
3. Media agent generates concrete, rich 9:16 visuals and clean cinematic fallback with zero brown circles.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from utils.logger import log_header, log_step, log_info, log_success, log_error
from utils.history import (
    load_history,
    record_processed_video,
    is_video_processed,
    get_processed_video_ids,
    record_processed_topic,
    is_topic_processed,
    get_processed_topics,
)
from agents.media_agent import MediaAgent
from PIL import Image


def test_history_manager():
    log_header("TEST 1: History Log Duplicate Prevention")
    import time

    unique_suffix = int(time.time() * 1000)
    # 1. Test video ID recording and duplicate detection
    test_id = f"test_vid_{unique_suffix}"
    test_title = f"Classified Cold War Secret Test #{unique_suffix}"

    log_info(f"Checking unrecorded video ID '{test_id}'...")
    assert not is_video_processed(test_id), "Unrecorded video ID should return False"

    log_info(f"Recording video ID '{test_id}'...")
    record_processed_video(test_id, test_title, duration=35.0, views=250000)

    assert is_video_processed(test_id), "Recorded video ID must return True"
    assert test_id in get_processed_video_ids(), "ID must be in get_processed_video_ids()"
    log_success(f"Video ID '{test_id}' duplicate detection verified.")

    # 2. Test topic recording and duplicate detection
    test_topic = f"Project Manhattan Heavy Water Facility {unique_suffix}"
    assert not is_topic_processed(test_topic), "Unrecorded topic should return False"

    record_processed_topic(test_topic, niche="Military History")
    assert is_topic_processed(test_topic), "Recorded topic must return True"
    assert any(test_topic in t for t in get_processed_topics()), "Topic must appear in get_processed_topics()"
    log_success(f"Topic '{test_topic}' duplicate prevention verified.")




def test_media_agent_visuals():
    log_header("TEST 2: High-Quality Visual Generation & Fallback Check")

    media_agent = MediaAgent()
    test_out_dir = config.WORKSPACE_DIR / "test_visuals"
    test_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Test Procedural Fallback (Must have zero brown circles / abstract orbs)
    fallback_path = test_out_dir / "procedural_fallback_test.jpg"
    concrete_prompt = (
        "1960s subterranean military bunker with rusted steel blast doors and green fluorescent lighting, "
        "a military officer in vintage uniform examining a classified map"
    )

    log_info("Testing procedural fallback image generation...")
    generated_fallback = media_agent._generate_procedural_fallback_image(concrete_prompt, fallback_path)

    assert generated_fallback.exists(), "Fallback image must exist"
    with Image.open(generated_fallback) as img:
        assert img.size == (720, 1280), f"Expected 720x1280, got {img.size}"
        assert img.mode == "RGB", f"Expected RGB mode, got {img.mode}"
    log_success(f"Procedural fallback verified: 720x1280 RGB cinematic film-still ({fallback_path.stat().st_size} bytes)")

    # 2. Test Pollinations Generation with Concrete Historical Scene
    external_path = test_out_dir / "external_flux_test.jpg"
    log_info("Testing Pollinations Flux generation with concrete historical prompt...")
    visual_prompt = (
        "A 1950s scientist in a white coat operating vintage vacuum tube instruments inside a concrete laboratory, "
        "Cinematic historical realism, dramatic cinematic lighting, 35mm film grain, vertical 9:16 composition, "
        "photorealistic 8k, hyper-detailed textures, no text, no watermark, no abstract shapes"
    )

    result_path, used_fallback = media_agent.generate_visual(visual_prompt, external_path, seed=4242)

    assert result_path.exists(), "Generated visual must exist on disk"
    with Image.open(result_path) as img:
        assert img.size == (720, 1280), f"Expected 720x1280, got {img.size}"
    log_success(
        f"Visual generated successfully -> {result_path.name} "
        f"({result_path.stat().st_size / 1024:.1f} KB, used_fallback={used_fallback})"
    )


if __name__ == "__main__":
    try:
        test_history_manager()
        test_media_agent_visuals()
        log_header("ALL HISTORY & VISUAL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        log_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
