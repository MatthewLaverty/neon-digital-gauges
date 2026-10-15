# v2 pipeline (2026-10-14)

The scripts use sandbox paths: `/home/user/workspace/scans2`, `../scans` for the v1 intermediates, and the repo. Run order:
1. reg_new.py: SIFT homographies from IMG_7574–7577 into the v1 master frame
2. ticks.py → rectify.py / rectify2.py → final_frame.py: tick extraction and the rectifying homography (circles + even steps + tape), with scale from the tape
3. master_v2.py: rectified mosaic, plus the v1 overlay geometry mapped into v2 (overlay_mm_v2.json)
4. reg_v2.py: per-gauge face↔hole check against IMG_7569
5. clean_v2.py (masks_v2.json) → comp_v2.py (color rules) → export_v2.py
6. needles_v2.py → needle_art_v2.py → ../mock.py, mockup_v2.py
7. gen_overlay_v2.py --reset, gen_scad_v2.py
8. rot.py: levels the frame (2.17° CCW, from text baselines); rerun steps 3–7 afterwards
