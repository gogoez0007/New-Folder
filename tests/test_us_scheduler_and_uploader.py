import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from google.auth.exceptions import RefreshError, TransportError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.analyst_writer_agent import AnalystWriterAgent
from agents.scout_agent import OFF_FORMAT_BLOCKLIST
from agents.subtitle_agent import SubtitleAgent, WordTiming
from agents.uploader_agent import YouTubeUploaderAgent, _trim_tags_under_500_chars
from core.background_story_core import BackgroundStoryCore
from schemas import CastMemberSchema, ProductionBatch, Scene, VideoScript, ViralBlueprint
from utils import history as history_mod
from utils.us_scheduler import compute_next_us_prime_slots


class TestUSSchedulerAndUploader(unittest.TestCase):
    def test_est_and_edt_dst_conversion(self):
        # Winter EST (UTC-5): 15:30 ET == 20:30Z, 19:00 ET == 00:00Z next day
        nov_now = datetime(2026, 11, 11, 16, 0, tzinfo=timezone.utc)
        nov_slots = compute_next_us_prime_slots(count=2, now_utc=nov_now, slots_et=["15:30", "19:00"])
        self.assertEqual(nov_slots[0]["publish_at_utc"], "2026-11-11T20:30:00Z")
        self.assertEqual(nov_slots[1]["publish_at_utc"], "2026-11-12T00:00:00Z")
        self.assertIn("EST", nov_slots[0]["publish_at_et"])

        # Summer EDT (UTC-4): 15:30 ET == 19:30Z, 19:00 ET == 23:00Z
        jul_now = datetime(2026, 7, 15, 16, 0, tzinfo=timezone.utc)
        jul_slots = compute_next_us_prime_slots(count=2, now_utc=jul_now, slots_et=["15:30", "19:00"])
        self.assertEqual(jul_slots[0]["publish_at_utc"], "2026-07-15T19:30:00Z")
        self.assertEqual(jul_slots[1]["publish_at_utc"], "2026-07-15T23:00:00Z")
        self.assertIn("EDT", jul_slots[0]["publish_at_et"])

    def test_reserved_slot_collision_avoidance(self):
        now = datetime(2026, 11, 11, 16, 0, tzinfo=timezone.utc)
        slots = compute_next_us_prime_slots(
            count=2,
            now_utc=now,
            slots_et=["15:30", "19:00"],
            reserved_utc_iso={"2026-11-11T20:30:00Z"},
        )
        self.assertEqual(slots[0]["publish_at_utc"], "2026-11-12T00:00:00Z")
        self.assertEqual(slots[1]["publish_at_utc"], "2026-11-12T20:30:00Z")

    def test_four_daily_slots_two_sessions_per_day(self):
        # Session 1 at 10:00 WIB == 03:00Z -> picks 08:00 ET & 12:30 ET same day
        run1_utc = datetime(2026, 11, 12, 3, 0, tzinfo=timezone.utc)
        batch1 = compute_next_us_prime_slots(count=2, now_utc=run1_utc, slots_et=["08:00", "12:30", "16:30", "20:00"])
        self.assertEqual([s["publish_at_et"] for s in batch1], ["2026-11-12 08:00 EST", "2026-11-12 12:30 EST"])
        reserved = {s["publish_at_utc"] for s in batch1}

        # Session 2 at 15:00 WIB == 08:00Z -> skips reserved 08:00/12:30 and picks 16:30 ET & 20:00 ET
        run2_utc = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)
        batch2 = compute_next_us_prime_slots(
            count=2,
            now_utc=run2_utc,
            slots_et=["08:00", "12:30", "16:30", "20:00"],
            reserved_utc_iso=reserved,
        )
        self.assertEqual([s["publish_at_et"] for s in batch2], ["2026-11-12 16:30 EST", "2026-11-12 20:00 EST"])

    def test_trim_tags_budget_and_dedup(self):
        raw = ["#Shorts", "shorts", "viral cartoon"] + [f"tagitem_{i}_abcdef" for i in range(60)]
        cleaned = _trim_tags_under_500_chars(raw)
        self.assertIn("Shorts", cleaned)
        self.assertTrue(sum(len(t) for t in cleaned) <= 460)
        self.assertFalse(any(t.startswith("#") for t in cleaned))

    def test_upload_short_metadata_dedup_and_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            fake_mp4 = tdir / "final_clip_1.mp4"
            fake_mp4.write_bytes(b"fake-video-bytes-123456")
            fake_thumb = tdir / "thumb.jpg"
            fake_thumb.write_bytes(b"fake-thumb-bytes")
            h1 = tdir / "hist_ws.json"
            h2 = tdir / "hist_out.json"
            saved_dir = tdir / "saved_clips"

            with patch.object(history_mod, "DEFAULT_HISTORY_FILE", h1), patch.object(history_mod, "MIRROR_HISTORY_FILE", h2):
                uploader = YouTubeUploaderAgent(
                    client_secrets_file=tdir / "cs.json",
                    token_file=tdir / "tok.json",
                    archive_dir=saved_dir,
                )
                mock_yt = MagicMock()
                req = MagicMock()
                req.next_chunk.return_value = (None, {"id": "ytVid123", "status": {"privacyStatus": "private"}})
                mock_yt.videos.return_value.insert.return_value = req
                uploader._service = mock_yt

                meta = {
                    "clip_index": 1,
                    "youtube_seo_title": "Leo Stair Challenge!",
                    "youtube_description": "Watch Leo climb!",
                    "outro_closing_line": "What will Toby do next?!",
                    "trending_tags": ["shorts", "3danimation"],
                }
                slot = {
                    "publish_at_utc": "2026-11-12T00:00:00Z",
                    "publish_at_et": "2026-11-11 19:00 EST",
                    "publish_at_wib": "2026-11-12 07:00 WIB",
                }
                rec = uploader.upload_short(fake_mp4, meta=meta, slot_info=slot, thumbnail_path=fake_thumb, privacy_mode="scheduled")
                self.assertEqual(rec["youtube_video_id"], "ytVid123")
                self.assertFalse(rec["skipped_duplicate"])
                archived_p1 = Path(rec["archived_mp4_path"])
                self.assertTrue(archived_p1.exists())
                self.assertTrue(Path(rec["archived_meta_path"]).exists())
                self.assertTrue(Path(rec["archived_thumbnail_path"]).exists())

                insert_kwargs = mock_yt.videos.return_value.insert.call_args.kwargs
                body = insert_kwargs["body"]
                self.assertEqual(body["snippet"]["defaultLanguage"], "en")
                self.assertEqual(body["snippet"]["defaultAudioLanguage"], "en-US")
                self.assertFalse(body["status"]["selfDeclaredMadeForKids"])
                self.assertEqual(body["status"]["publishAt"], "2026-11-12T00:00:00Z")

                # Second upload of identical file bytes must skip as duplicate
                rec2 = uploader.upload_short(fake_mp4, meta=meta, slot_info=slot, privacy_mode="scheduled")
                self.assertTrue(rec2["skipped_duplicate"])

                # Next batch overwriting final_clip_1.mp4 must archive alongside previous clip without deleting it
                fake_mp4.write_bytes(b"new-batch-video-bytes-999")
                req.next_chunk.return_value = (None, {"id": "ytVid456", "status": {"privacyStatus": "private"}})
                rec3 = uploader.upload_short(fake_mp4, meta=meta, slot_info=slot, privacy_mode="scheduled")
                archived_p2 = Path(rec3["archived_mp4_path"])
                self.assertTrue(archived_p1.exists())
                self.assertTrue(archived_p2.exists())
                self.assertNotEqual(archived_p1, archived_p2)

    def test_check_auth_status_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            tok = tdir / "youtube_token.json"
            uploader = YouTubeUploaderAgent(client_secrets_file=tdir / "cs.json", token_file=tok)

            # 1. Missing token
            st = uploader.check_auth_status()
            self.assertTrue(st["needs_auth"])
            self.assertEqual(st["reason"], "missing_token")

            # 2. Corrupt JSON token
            tok.write_text("{not-json", encoding="utf-8")
            st = uploader.check_auth_status()
            self.assertTrue(st["needs_auth"])
            self.assertEqual(st["reason"], "corrupt_token")

            # 3. Valid token must NOT trigger by elapsed age — only live refresh result matters
            granted = datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)
            tok.write_text(json.dumps({"token": "a", "refresh_token": "r"}), encoding="utf-8")
            uploader._record_interactive_auth_timestamp(granted_at=granted)

            fake_creds = MagicMock()
            fake_creds.refresh_token = "r"
            fake_creds.to_json.return_value = json.dumps({"token": "new_a", "refresh_token": "r"})
            with patch("agents.uploader_agent.Credentials.from_authorized_user_file", return_value=fake_creds):
                st_ok = uploader.check_auth_status()
                self.assertFalse(st_ok["needs_auth"])
                self.assertEqual(st_ok["reason"], "valid")

                # 4. Revoked / invalid_grant RefreshError triggers immediately
                fake_creds.refresh.side_effect = RefreshError("invalid_grant: Token has been expired or revoked.")
                st_revoked = uploader.check_auth_status()
                self.assertTrue(st_revoked["needs_auth"])
                self.assertEqual(st_revoked["reason"], "expired_or_revoked")

                # 5. Transient offline TransportError must NOT false-alarm
                fake_creds.refresh.side_effect = TransportError("HTTPSConnectionPool: Max retries exceeded")
                st_offline = uploader.check_auth_status()
                self.assertFalse(st_offline["needs_auth"])
                self.assertEqual(st_offline["reason"], "offline_network_error")


class TestRetentionUpgrades(unittest.TestCase):
    def test_subtitle_ass_hook_banner_and_two_word_pacing(self):
        agent = SubtitleAgent()
        words = [
            WordTiming(word=w, start=i * 0.25, end=(i + 1) * 0.25)
            for i, w in enumerate(["Wait", "dont", "touch", "that", "cake"])
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out_ass = Path(tmp) / "hook_test.ass"
            agent.generate_ass_subtitles(
                words=words,
                output_ass_path=out_ass,
                words_per_chunk=2,
                emphasis_keywords=["CAKE"],
                hook_headline="CAKE PRANK?!",
            )
            ass_text = out_ass.read_text(encoding="utf-8")

        self.assertIn("Style: HookBanner", ass_text)
        self.assertIn("0:00:00.00,0:00:02.35,HookBanner", ass_text)
        self.assertIn("CAKE PRANK?!", ass_text)
        caption_lines = [
            line for line in ass_text.splitlines()
            if line.startswith("Dialogue:") and ",HookBanner," not in line
        ]
        # 5 words emit 5 karaoke events grouped in max 2-word chunks
        self.assertEqual(len(caption_lines), 5)
        self.assertIn("WAIT", caption_lines[0])
        self.assertIn("DONT", caption_lines[0])
        self.assertNotIn("TOUCH", caption_lines[0])
        self.assertIn("CAKE", caption_lines[-1])
        self.assertIn("\\c&H0000FF00&", caption_lines[-1])

    def test_cozy_village_oak_trees_do_not_clip_houses(self):
        _env, props = BackgroundStoryCore().build_world_props("cozy_village")
        trees = [p for p in props if p.prop_type == "oak_tree"]
        houses = [p for p in props if p.prop_type == "house_building"]
        self.assertTrue(trees)
        self.assertTrue(houses)
        for tree in trees:
            for house in houses:
                dist = math.hypot(
                    tree.position[0] - house.position[0],
                    tree.position[2] - house.position[2],
                )
                self.assertGreaterEqual(dist, 2.2)

    def test_enrich_distinct_cliffhangers_preserves_zero_outro_epilogue(self):
        writer = AnalystWriterAgent.__new__(AnalystWriterAgent)
        writer.client = None
        blueprint = ViralBlueprint(
            hook_strategy="Immediate frame-0 action",
            pacing_and_rhythm="Fast 2s cuts",
            visual_style="3D cartoon",
            narrative_arc="Setup-twist-payoff",
        )
        scripts = [
            VideoScript(
                clip_index=idx,
                title=f"Funny 3D Cake Prank #{idx} #shorts",
                hook_text="Wait dont touch that!",
                target_niche="3d comedy",
                cast_roles=[CastMemberSchema(name="Leo", archetype="hero_boy", role="protagonist")],
                scenes=[
                    Scene(scene_number=1, narration="Wait dont touch that!", is_outro_epilogue=False),
                    Scene(scene_number=2, narration="Oh no the cake flew!", is_outro_epilogue=False),
                ],
            )
            for idx in (1, 2)
        ]
        batch = ProductionBatch(viral_blueprint=blueprint, generated_scripts=scripts)
        writer.enrich_distinct_cliffhangers(batch, force=True, repair_main_climax=True)

        for sc in batch.generated_scripts:
            self.assertEqual(len(sc.scenes), 2)
            self.assertTrue(all(not s.is_outro_epilogue for s in sc.scenes))

    def test_scout_blocklist_filters_off_format_allows_3d_pranks(self):
        blocked_titles = [
            "save them from titanic axolotl",
            "he chased a thief turkey mother's love",
            "funny 2d animation flipaclip",
        ]
        for title in blocked_titles:
            self.assertTrue(any(bad in title for bad in OFF_FORMAT_BLOCKLIST), msg=title)

        allowed_title = "funny 3d animation cake prank cartoon"
        self.assertFalse(any(bad in allowed_title for bad in OFF_FORMAT_BLOCKLIST))


if __name__ == "__main__":
    unittest.main()

