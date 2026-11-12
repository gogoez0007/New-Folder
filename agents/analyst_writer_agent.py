"""
Viral Analyst & Scriptwriter Agent (Agents 2 & 3).
Uses Google GenAI SDK to upload and analyze reference Shorts (multimodal vision + audio),
extracting the viral blueprint and generating 2 to 4 high-retention vertical video scripts
and storyboards formatted via Pydantic structured outputs.
"""

import json
import time
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

import config
from schemas import ProductionBatch, Scene
from utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_scene,
)
from utils.history import (
    get_processed_topics,
    record_processed_topic,
)


class _CliffhangerItem(BaseModel):
    clip_index: int
    outro_closing_line: str = Field(..., description="Short 3-6 word creative curiosity-inducing closing line spoken in the SEPARATE 1-2s outro segment AFTER main scenes (e.g. 'What should Leo do next?!', 'Wait for Coco Part Two!').")
    main_climax_narration: str = Field(default="", description="Faithful 5-8 word narration matching the final main scene action summary (only used when repairing previously overwritten plans).")
    cliffhanger_hook: str = Field(..., description="Distinct curiosity question or Part-2 hook leaving viewers guessing what happens next.")
    cliffhanger_badge_text: str = Field(..., description="3-5 word ALL-CAPS cover/outro curiosity question unique to this story (e.g. 'WHAT WILL TOBY DO?!').")
    outro_vfx_style: str = Field(..., description="One of: portal_vortex_zoom, iris_freeze_question, shockwave_spark_spin, shatter_flash_glint.")
    final_sfx_cue: str = Field(default="magic_chime", description="One of: magic_chime, gasp_shock.")
    closing_hero_action: str = Field(default="recoil_surprise", description="One of: recoil_surprise, point_discover, plead_camera_help, cheer_celebrate.")
    closing_hero_expression: str = Field(default="shocked", description="One of: shocked, curious, surprised, excited, determined.")


class _CliffhangerBatch(BaseModel):
    endings: List[_CliffhangerItem] = Field(default_factory=list)



class AnalystWriterAgent:
    """Agent responsible for reverse-engineering viral mechanics and writing synchronized scripts."""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or config.GEMINI_API_KEY
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please add your key to .env file."
            )
        self.client = genai.Client(api_key=key)

    def _wait_for_file_active(self, uploaded_file) -> None:
        """Wait for the uploaded video to finish processing on Google GenAI servers."""
        log_info(f"Waiting for video processing: {uploaded_file.name} (state: {uploaded_file.state.name})")
        start_time = time.time()
        file_obj = uploaded_file

        while file_obj.state.name == "PROCESSING":
            if time.time() - start_time > 180:
                raise TimeoutError("Timed out waiting for video processing on Google servers.")
            time.sleep(3)
            file_obj = self.client.files.get(name=file_obj.name)
            log_info(f"Video processing status: {file_obj.state.name} ({int(time.time() - start_time)}s elapsed)")

        if file_obj.state.name == "FAILED":
            raise RuntimeError(
                f"Video processing failed on Google server: {getattr(file_obj, 'error', 'Unknown error')}"
            )
        log_success("Remote video is ACTIVE and ready for multimodal analysis.")

    def analyze_and_generate(
        self,
        video_path: Path,
        target_niche: str,
        clip_count: int = 2,
        language: str = "en",
        reference_title: Optional[str] = None,
        reference_duration: Optional[float] = None,
        video_paths: Optional[List[Path]] = None,
        video_durations: Optional[List[float]] = None,
        reference_titles: Optional[List[str]] = None,
    ) -> ProductionBatch:
        """
        Uploads viral 3D animation video(s), extracts the viral blueprint, and synthesizes 2-4
        fresh Kids 3D Animation scripts synchronized to real moving 3D animation scenes.
        """
        all_paths = [Path(p).resolve() for p in (video_paths or [video_path])]
        for p in all_paths:
            if not p.exists():
                raise FileNotFoundError(f"Reference video not found at: {p}")

        clip_count = max(2, min(4, clip_count))
        log_info(
            f"Initiating Multimodal 3D Animation Analysis on {len(all_paths)} viral video(s) "
            f"-> Generating {clip_count} kids 3D animation scripts in niche: '{target_niche}' ({language})"
        )

        uploaded_files = []
        try:
            for idx, p in enumerate(all_paths, 1):
                log_info(f"Uploading Viral 3D Animation #{idx} ({p.name}) to Google GenAI...")
                uf = self.client.files.upload(file=str(p))
                log_success(f"Video #{idx} uploaded. File ID: {uf.name}")
                self._wait_for_file_active(uf)
                uploaded_files.append(uf)

            past_topics = get_processed_topics()
            past_topics_section = ""
            if past_topics:
                past_list_str = "\n".join(f"  * {topic}" for topic in past_topics[-30:])
                past_topics_section = f"""
STRICT TOPIC UNIQUENESS - FORBIDDEN PREVIOUS TITLES:
{past_list_str}
You MUST write 100% BRAND NEW, imaginative kids story titles and narratives!
"""

            dur_info_lines = []
            for idx, p in enumerate(all_paths, 1):
                d_sec = (
                    video_durations[idx - 1]
                    if video_durations and idx - 1 < len(video_durations)
                    else (reference_duration or 30.0)
                )
                r_title = (
                    reference_titles[idx - 1]
                    if reference_titles and idx - 1 < len(reference_titles)
                    else (reference_title if idx == 1 else f"Video #{idx}")
                )
                dur_info_lines.append(
                    f"  - Video #{idx} (`source_video_index={idx}`, title=\"{r_title}\"): duration = {d_sec:.1f} seconds"
                )
            dur_info_str = "\n".join(dur_info_lines)

            prompt = f"""
You are the Lead 3D Animation Scene Deconstructor & Director for a viral 3D Animation Shorts studio.
We have attached {len(uploaded_files)} trending 3D animated YouTube Short reference video(s):
{dur_info_str}

YOUR CORE MISSION (HIGH-RETENTION 3D SHORTS RECREATION — 100% HONEST TO SCREEN ASSETS):
1. Watch each attached trending reference video carefully from 0.0s to the end.
2. CRITICAL ASSET FIDELITY — WRITE ONLY CHARACTERS & WORLDS OUR 3D ENGINE CAN RENDER:
   Our 3D engine renders **stylized 3D human/chibi characters** (`hero_boy`, `hero_girl`, `suited_executive`, `sporty_athlete`, `elder_mentor`, `villain_boss`, `robot_assistant`) plus **`pet_dog` (`ShibaInu`/`Husky`)** and **`dinosaur`/`monster`** (`tiny_prank_critter`, `large_goofy_creature`), inside 3D biomes (`cozy_village`, `city_playground`, `waterpark_pool`, `golden_city`, `stone_maze`, `indoor_room`, `beach_island`, `futuristic_lab`, `school_courtyard`, `magic_carnival`, `jungle_safari`).
   - **NEVER title, narrate, or name un-renderable species/scenes** (e.g. NEVER say "turkey", "mouse", "axolotl", "platypus", or "Titanic sinking"!). If a reference features non-engine creatures (like birds/mice/2D blobs), cleanly cast them as stylized 3D heroes/kids, mischievous critters, robots, or dogs matching `cast_roles` AND write the **title, hook, dialogue, and props 100% consistently** with what viewers WILL actually see on screen! Setting `has_background_crowd=false` keeps framing clean unless a crowd is essential.
3. RETENTION-ENGINEERED 11–15s STRUCTURE (`4 to 5` PUNCHY SCENES PER CLIP):
   - **Scene #1 (`0.0–2.2s`, `4–6 words` MAX, `duration_target: 2.0`) MUST start IN MEDIA RES with a scroll-stopping hook/stakes/conflict** (`"Wait—DON'T open Rex's mystery box!"`, `"One wrong step drops Toby!"`, `"He rigged Leo's birthday cake?!"`) — ZERO slow greetings or boring exposition!
   - Keep **total estimated duration tight (`11.0–15.0s` across `4 to 5` fast scenes, `2.2–3.2s` each)** so retention stays high!
   - Keep each scene's spoken `narration` **punchy (4–8 words MAX)**, high-stakes, visually reactive to what happens on screen, and NEVER repetitive across scenes!
   - **NO FAKE "PART 2 / COMMENT BELOW" PROMO BUMPER AT THE END!** End directly on the shocking payoff, funny reversal, or crisp final reaction (`is_outro_epilogue=false` on all story scenes) so viewers finish the whole Short and loop right back!
   - **Script #1 (`clip_index=1`)** recreates Video #1 (`source_video_index=1`); **Script #2 (`clip_index=2`)** recreates Video #{2 if len(uploaded_files) >= 2 else 1} (`source_video_index={2 if len(uploaded_files) >= 2 else 1}`) with its own distinct cast, biome, props, and hook!
{past_topics_section}
CRITICAL FIDELITY, CHOREOGRAPHY & ANTI-JUMPING RULES:
1. ZERO HALLUCINATED CAST OR UNRELATED PROPS, AND ZERO GRATUITOUS JUMPING:
   - Use `focus_character` (`"both"`, `"lead"`, or `"partner"`) to match who is on screen in that reference shot!
   - Choose `scene_staging_mode` accurately from the reference frame composition:
     * `"table_challenge_front"`: Characters sit or stand BEHIND a foreground table with food/items/challenge props resting ON TOP OF the table facing the camera (e.g., taste test, blind food challenge, cake/cone/cactus prank, cup game). Keep tabletop props in `scene_props` alongside `"wooden_table"`.
     * `"course_climb_progression"`: Characters climb or run across raised stairs, platforms, stepping pads, or obstacle blocks (use `"musical_staircase"` when colorful musical stairs/steps appear!). ALWAYS set `lead_elevation_m` to actual height (`0.4 -> 1.2 -> 1.6`, or `0.0` when falling/landing on ground)!
     * `"elevated_vantage"`: Character perched on a wall, tree, truck, or hydraulic lift.
     * `"chase_corridor"` or `"general"`.
   - NEVER use `"none"` for `lead_expression`, `partner_expression`, or `partner_action`! Use `"neutral"` or `"curious"` for expressions and `"idle"` when a character is absent/silent.
   - ALWAYS emit REAL `source_start_sec` & `source_end_sec` timestamps in seconds across the full video duration (e.g., `0.0 -> 2.1`, `2.1 -> 4.3`, ..., up to total duration — NEVER `0.01..0.02`!).
   - Vary `camera_shot_style` naturally across consecutive scenes while matching the reference shot framing.
   - DO NOT MAKE CHARACTERS JUMP unless they literally jump in that scene of the reference video!
     * Locomotion: `"walk_casual"`, `"run_urgent"`, `"sneak_tiptoe"`
     * Conversation & Reactions: `"talk_explain"`, `"listen_nod"`, `"shake_head_no"`, `"point_discover"`, `"recoil_surprise"`, `"laugh_giggle"`
     * Object & Prop Interaction: `"interact_use_prop"`, `"pick_up_inspect"`, `"give_or_share"`, `"push_or_block"`
     * Postures & Emotions: `"sit_floor_relax"`, `"sit_chair_or_bench"`, `"lie_down_exhausted"`, `"sad_cry_slump"`, `"plead_camera_help"`
     * Celebration: `"cheer_celebrate"`, `"dance_groove"`, and ONLY use `"jump_obstacle_or_joy"` if jumped in that specific scene!
2. EXACT BIOME (`world_biome`) & SCENE PROPS (`scene_props`) MATCHING EACH REFERENCE VIDEO:
   - `world_biome`: `"golden_city"`, `"lush_forest"`, `"indoor_room"`, `"stone_maze"`, `"waterpark_pool"`, `"school_courtyard"`, `"city_playground"`, `"magic_carnival"`, `"jungle_safari"`, `"futuristic_lab"`, `"beach_island"`, `"cozy_village"`.
   - ALWAYS populate `scene_props` for EVERY scene that shows objects! Prefer canonical IDs (`"giant_cockroach"`, `"cooking_pot"`, `"cleaning_broom"`, `"computer_desk"`, `"stone_maze_walls"`, `"laser_beam"`, `"hero_shield"`, `"angry_bull"`, `"camouflage_bush"`, `"strength_orb"`, `"skyscraper_city"`, `"hydraulic_lift_chair"`, `"flying_airplane"`, `"hollow_tree_trunk"`, `"jungle_giant_leaf"`, `"balloon_bundle_red"`, `"sausage_prop"`, `"ocean_water_plane"`, `"cage_trap"`, `"mystery_table"`, `"race_finish_arch"`, `"inflatable_pool"`, `"water_slide"`, `"treasure_chest"`, `"park_bench"`, `"magic_portal"`, `"control_pedestal"`, `"gift_box_pile"`, `"obstacle_hurdle"`, `"campfire_ring"`, `"stage_podium"`, `"bridge_span"`, `"book_and_coin_stacks"`, `"color_archways"`, `"color_cubes"`, `"trophy_display"`, `"bouncer_pad"`, `"water_boat"`, `"moving_car"`, `"beach_umbrella"`, `"balloon_bunch"`, `"skateboard"`, `"sofa_couch"`) or clear snake_case names matching what is visible!
3. EXPRESSIONS, SPATIAL BLOCKING & SFX (AUTONOMOUS LEARNING ENABLED):
   - `lead_expression` & `partner_expression`: describe the exact expression visible (`"happy"`, `"excited"`, `"curious"`, `"surprised"`, `"shocked"`, `"sad"`, `"crying"`, `"angry"`, `"determined"`, `"embarrassed"`, `"proud"`, `"laughing"` — OR if another nuanced mimic appears like `"smirking"`, `"winking"`, `"chewing"`, `"panicked"`, `"disgusted"`, `"sleepy_yawn"`, `"confused_squint"`, use that exact snake_case term so the Expression Learning Core synthesizes it!).
   - Also describe ANY unseen prop in `scene_props` with a clear snake_case ID (e.g. `"handphone"`, `"smartphone"`, `"microphone"`, `"basketball"`, etc.) — the Meta-Core Synthesizer automatically generates its 3D Object Core!
   - `spatial_pattern`: `"approach_center"`, `"left_to_right_travel"`, `"right_to_left_travel"`, `"face_to_face_dialogue"`, `"chase_pursuit"`, `"gather_around_prop"`, `"step_back_recoil"`, `"walk_to_camera"`, `"side_by_side_walk"`, `"stationary_focus"`.
   - `sfx_cue`: `"whoosh"`, `"pop"`, `"beep"`, `"impact"`, `"splash"`, `"boing"`, `"magic_chime"`, `"cheer_fanfare"`, `"sad_trombone"`, `"gasp_shock"`, `"footsteps"`, `"laugh_giggle"`.
   - `source_start_sec` and `source_end_sec`: Exact chronological timestamps `[start, end]` of that scene in the reference video.
4. CLICK-WORTHY YOUTUBE TITLE, COVER HEADLINE & TRENDING TAGS (per Script):
   - `youtube_seo_title`: Punchy high-CTR curiosity title (< 85 chars) with emoji + `#shorts` (e.g., `"Cake for Rex... Wait WHAT's Under Coco's Box?! 😱🌵 #shorts"`).
   - `thumbnail_headline`: Ultra-bold 2–4 word ALL-CAPS cover text (`"CACTUS PRANK?!"`, `"WHO REACHES TOP?!"`).
   - `youtube_description`: Exciting 2-sentence description asking viewers to LIKE & SUBSCRIBE + hashtags (`#shorts #3danimation #funny`).
   - `trending_tags`: 12–16 high-volume discovery tags (lowercase, no `#`, mix of `3d animation`, `viral shorts`, `funny animation`, `kids 3d story`, `animated comedy`, plus clip-specific object/challenge terms).
5. CREATIVE NON-REPETITIVE CLIFFHANGER EPILOGUE & OUTRO VFX (CRITICAL):
   - Keep EVERY MAIN SCENE (`1..N`) 100% faithful to the reference video story & climax — do NOT replace or overwrite the final main scene with an outro teaser!
   - Instead, put a gripping **3 to 6 word** spoken curiosity question/cliffhanger for a **SEPARATE 1–2 second outro epilogue scene** into `cliffhanger_hook` (e.g., Clip #1 dilemma like *"Wait, what will Toby find?!"* vs Clip #2 Part-2 teaser like *"Coco in Part Two... wait!"* — NEVER repeat the same structure across clips!).
   - Fill `cliffhanger_badge_text` (3–5 bold ALL-CAPS words unique per clip) and choose DIFFERENT `outro_vfx_style` values (`"portal_vortex_zoom"`, `"iris_freeze_question"`, `"shockwave_spark_spin"`, `"shatter_flash_glint"`) across clips!
"""

            candidate_models = ["gemini-3-flash-preview", config.MODEL_ID, config.FALLBACK_MODEL_ID, "gemini-3.1-flash-lite-preview", "gemini-3.5-flash-lite"]
            models_to_try = []
            for m in candidate_models:
                if m and m not in models_to_try:
                    models_to_try.append(m)

            response = None
            last_err = None

            for model_name in models_to_try:
                try:
                    log_info(f"Attempting Structured 3D Animation Analysis using model: '{model_name}'...")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[*uploaded_files, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ProductionBatch,
                            temperature=0.7,
                        ),
                    )
                    log_success(f"Received structured response from '{model_name}'.")
                    break
                except Exception as e:
                    log_warning(f"Model '{model_name}' failed: {e}. Trying fallback if available...")
                    last_err = e

            if response is None:
                raise RuntimeError(f"All Gemini models failed to generate content. Last error: {last_err}")

            # 5. Extract and Validate ProductionBatch
            if hasattr(response, "parsed") and isinstance(response.parsed, ProductionBatch):
                production_batch = response.parsed
            else:
                raw_json = response.text
                production_batch = ProductionBatch.model_validate_json(raw_json)

            # Enrich reference metadata if missing
            if not production_batch.reference_title and reference_title:
                production_batch.reference_title = reference_title
            if not production_batch.reference_duration_seconds and reference_duration:
                production_batch.reference_duration_seconds = reference_duration

            # Record generated script topics into history log to guarantee no future duplication
            for script in production_batch.generated_scripts:
                record_processed_topic(
                    title=script.title,
                    niche=target_niche,
                    clip_index=script.clip_index,
                )

            # Ensure every clip finishes with a unique, non-hardcoded curiosity cliffhanger + distinct outro VFX!
            self.enrich_distinct_cliffhangers(production_batch, force=False)

            # 6. Save production plan to workspace and output directories
            self._save_plan(production_batch)
            self._log_summary(production_batch)

            return production_batch

        finally:
            # 7. Always delete remote files from Google servers to keep cloud clean
            for uf in uploaded_files:
                try:
                    log_info(f"Cleaning up remote file from Google servers: {uf.name}")
                    self.client.files.delete(name=uf.name)
                    log_success("Remote video deleted successfully from Google GenAI storage.")
                except Exception as e:
                    log_warning(f"Could not delete remote file {uf.name}: {e}")

    def enrich_distinct_cliffhangers(
        self,
        batch: ProductionBatch,
        force: bool = False,
        repair_main_climax: bool = False,
    ) -> None:
        """
        Keep ALL main story scenes intact and APPEND a dedicated 1–2 second closing epilogue scene
        (`is_outro_epilogue=True`) with a unique, non-repetitive curiosity line & signature 3D outro VFX.
        """
        scripts = list(batch.generated_scripts or [])
        if not scripts:
            return

        need_refresh = force or repair_main_climax or any(
            not (getattr(sc, "cliffhanger_hook", "") or "").strip()
            or not (getattr(sc, "cliffhanger_badge_text", "") or "").strip()
            or not any(bool(getattr(s, "is_outro_epilogue", False)) for s in (sc.scenes or []))
            for sc in scripts
        )
        used_styles = [getattr(sc, "outro_vfx_style", "") for sc in scripts]
        if len(set(used_styles)) < len(scripts):
            need_refresh = True

        if not need_refresh:
            return

        clip_briefs = []
        for sc in scripts:
            main_scenes = [s for s in (sc.scenes or []) if not getattr(s, "is_outro_epilogue", False)] or list(sc.scenes or [])
            last_main = main_scenes[-1] if main_scenes else None
            cast_names = [c.name for c in (sc.cast_roles or [])] or ["Leo"]
            props = sorted({p for s in main_scenes for p in (s.scene_props or [])})
            clip_briefs.append({
                "clip_index": sc.clip_index,
                "title": sc.title,
                "language": sc.language or "en",
                "cast": cast_names,
                "props": props,
                "previous_narration": [s.narration for s in main_scenes[:-1]],
                "last_main_narration": last_main.narration if last_main else sc.hook_text,
                "last_main_summary": getattr(last_main, "ref_scene_action_summary", "") if last_main else "",
            })

        styles_all = ["portal_vortex_zoom", "iris_freeze_question", "shockwave_spark_spin", "shatter_flash_glint"]
        allowed_actions = ["recoil_surprise", "point_discover", "plead_camera_help", "cheer_celebrate"]
        allowed_exprs = ["shocked", "curious", "surprised", "excited", "determined"]
        prompt = f"""
You are an expert viral YouTube Shorts story doctor.
We keep ALL main scenes (`1..N`) untouched as the core story, and append ONE EXTRA 1.5-SECOND CLOSING OUTRO SEGMENT at the very end!
Generate ONLY the creative 1–2s closing epilogue segment metadata for each clip below.

CLIPS DATA:
{json.dumps(clip_briefs, indent=2)}

STRICT RULES:
1. Match each clip's `language` (e.g., if `en`, natural kids-friendly English; if `id`, natural Indonesian).
2. Write `outro_closing_line` as **3 to 6 words MAX** so it speaks cleanly in **1.3–1.9 seconds**! Each clip MUST use a **100% DIFFERENT, CREATIVE, NON-REPETITIVE cliffhanger structure** anchored directly in THAT clip's focal hero & key object:
   - Clip #1 pattern example: dilemma question (e.g. "What should Toby do next?!")
   - Clip #2 pattern example: Part-2 cliffhanger tease (e.g. "Coco's cactus secret, Part Two!")
   NEVER reuse the same opening phrasing or sentence template across Clip #1 and Clip #2!
3. Fill `main_climax_narration` with a vivid 4–8 word story narration describing `last_main_summary` using THAT clip's swapped character name from `cast` (NEVER generic words like "Small boy" or "Man" — e.g. "Toby leaps onto the top musical step!" or "Coco screams at the prickly cactus!"), completely separate from the outro!
4. Set `cliffhanger_badge_text` to 3–5 bold ALL-CAPS words unique to that clip (`WHAT WILL TOBY DO?!`, `CACTUS SECRET PART 2?!`, etc.).
5. Assign DIFFERENT `outro_vfx_style` values across clips from: {styles_all}.
6. Choose `closing_hero_action` from {allowed_actions} and `closing_hero_expression` from {allowed_exprs}.
"""
        parsed_endings: Optional[_CliffhangerBatch] = None
        if self.client:
            tried = set()
            for mname in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite-preview", "gemini-3-flash-preview"]:
                if mname in tried:
                    continue
                tried.add(mname)
                try:
                    resp = self.client.models.generate_content(
                        model=mname,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=_CliffhangerBatch,
                            temperature=0.92,
                        ),
                    )
                    parsed_endings = (
                        resp.parsed
                        if hasattr(resp, "parsed") and isinstance(resp.parsed, _CliffhangerBatch)
                        else _CliffhangerBatch.model_validate_json(resp.text)
                    )
                    if parsed_endings and parsed_endings.endings:
                        log_success(f"[AnalystWriterAgent] Synthesized distinct 1-2s outro epilogues via '{mname}'.")
                        break
                except Exception as err:
                    log_warning(f"[AnalystWriterAgent] Outro epilogue synth ({mname}) skipped: {err}")

        by_idx = {e.clip_index: e for e in (parsed_endings.endings if parsed_endings else [])}
        used_final_styles = set()
        for pos_i, sc in enumerate(scripts):
            main_scenes = [s for s in (sc.scenes or []) if not getattr(s, "is_outro_epilogue", False)] or list(sc.scenes or [])
            hero = sc.cast_roles[-1].name if sc.cast_roles else (sc.cast_roles[0].name if sc.cast_roles else "Leo")
            hero0 = sc.cast_roles[0].name if sc.cast_roles else "Leo"
            last_main = main_scenes[-1] if main_scenes else None
            last_prop = (last_main.scene_props[0].replace("_", " ") if (last_main and last_main.scene_props) else "mystery prize")

            item = by_idx.get(sc.clip_index)
            if item and item.outro_closing_line.strip():
                if repair_main_climax and last_main and item.main_climax_narration.strip():
                    last_main.narration = item.main_climax_narration.strip()
                closing_line = item.outro_closing_line.strip()
                sc.cliffhanger_hook = (item.cliffhanger_hook or closing_line).strip()
                sc.cliffhanger_badge_text = item.cliffhanger_badge_text.strip().upper()[:34]
                style_cand = item.outro_vfx_style if item.outro_vfx_style in styles_all else styles_all[pos_i % len(styles_all)]
                sfx_cand = item.final_sfx_cue if item.final_sfx_cue in ("magic_chime", "gasp_shock") else "magic_chime"
                hero_act = item.closing_hero_action if item.closing_hero_action in allowed_actions else "recoil_surprise"
                hero_expr = item.closing_hero_expression if item.closing_hero_expression in allowed_exprs else "shocked"
            else:
                templates = [
                    (
                        f"What should {hero} do next?!",
                        f"What should {hero} do next with that {last_prop}?",
                        f"WHAT WILL {hero.upper()} DO?!",
                        "gasp_shock",
                        "recoil_surprise",
                        "curious",
                    ),
                    (
                        f"Wait for {hero} Part Two!",
                        f"Stay tuned for {hero0} and {hero}'s Part Two twist!",
                        f"{hero.upper()} PART TWO?!",
                        "magic_chime",
                        "point_discover",
                        "shocked",
                    ),
                    (
                        f"Can {hero} unlock the secret?!",
                        f"Will {hero} uncover the hidden {last_prop} secret next?",
                        f"SECRET {last_prop.upper()[:14]}?!",
                        "magic_chime",
                        "plead_camera_help",
                        "surprised",
                    ),
                ]
                closing_line, ch, badge, sfx_cand, hero_act, hero_expr = templates[pos_i % len(templates)]
                sc.cliffhanger_hook = ch
                sc.cliffhanger_badge_text = badge[:34]
                style_cand = styles_all[pos_i % len(styles_all)]

            # Hard cap spoken closing sentence to <= 7 words so it always fits cleanly inside 1-2s
            words_cl = closing_line.split()
            if len(words_cl) > 7:
                closing_line = " ".join(words_cl[:6]).rstrip(",.;:") + "?!"

            while style_cand in used_final_styles and len(used_final_styles) < len(styles_all):
                style_cand = styles_all[(styles_all.index(style_cand) + 1) % len(styles_all)]
            used_final_styles.add(style_cand)
            sc.outro_vfx_style = style_cand  # type: ignore[assignment]

            w_emph = [w.strip("?!.,-") for w in closing_line.split() if len(w.strip("?!.,-")) >= 3]
            if w_emph and last_main and not getattr(last_main, "subtitle_emphasis_words", None):
                last_main.subtitle_emphasis_words = w_emph[-2:]
            # Keep pure story climax without appending a separate Part-2 promo bumper (prevents <20% end drop-off!)
            sc.scenes = main_scenes
            sc.estimated_duration = round(sum(float(getattr(s, "duration_target", 2.5) or 2.5) for s in sc.scenes), 2)

    def _save_plan(self, batch: ProductionBatch) -> None:
        """Save the validated production plan JSON to workspace and output folders."""
        json_data = batch.model_dump_json(indent=2)

        workspace_plan = config.WORKSPACE_DIR / "production_plan.json"
        output_plan = config.OUTPUT_DIR / "production_plan.json"

        workspace_plan.write_text(json_data, encoding="utf-8")
        output_plan.write_text(json_data, encoding="utf-8")

        log_success(f"Production plan saved to: {workspace_plan}")
        log_success(f"Production plan saved to: {output_plan}")

    def _log_summary(self, batch: ProductionBatch) -> None:
        """Pretty-print viral blueprint and script storyboard summary."""
        blueprint = batch.viral_blueprint
        print("\n" + "=" * 70)
        print("  VIRAL BLUEPRINT EXTRACTED")
        print("=" * 70)
        print(f"[*] Hook Strategy:   {blueprint.hook_strategy}")
        print(f"[*] Concept Formula: {blueprint.concept_formula}")
        print(f"[*] Cut Speed:       {blueprint.scene_cut_frequency_seconds:.1f}s average")
        print(f"[*] Pacing & Rhythm: {blueprint.pacing_and_rhythm}")
        print(f"[*] Visual Style:    {blueprint.visual_style}")
        print(f"[*] Narrative Arc:   {blueprint.narrative_arc}")
        print(f"[*] Retention Cues:  {', '.join(blueprint.retention_tactics)}")

        print("\n" + "=" * 70)
        print(f"  GENERATED SCRIPTS ({len(batch.generated_scripts)} CLIPS)")
        print("=" * 70)
        for script in batch.generated_scripts:
            print(f"\n[Clip #{script.clip_index}] {script.title}")
            print(f"   Hook: \"{script.hook_text}\"")
            print(f"   Scenes ({len(script.scenes)} total, ~{script.estimated_duration:.1f}s):")
            for sc in script.scenes:
                log_scene(sc.scene_number, sc.duration_target, sc.camera_motion, sc.narration)
        print("=" * 70 + "\n")
