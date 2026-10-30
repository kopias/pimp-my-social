"""One makeover, start to finish, in two acts with the owner's choice in between.

Act one (inspect): render the site, score it, read the brand, offer paint jobs.
Then the owner picks a direction. Act two (build): photo studio, website, social
kit, video, the after audit, the report, the brand skill, the download.

State lives in out/jobs/<id>/job.json after every step, so the page can poll it
and a finished makeover can be reopened (and replayed in a demo) any time.
"""

from __future__ import annotations

import asyncio
import json
import random
import shutil
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from . import audit, brand, campaign, directions, logo, mockups, photos, remix, report, site, skill, social
from .crawl import Site, inspect

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "out" / "jobs"

STAGES = [
    ("inspect", "Inspection", "Rendering the site like a visitor, a search engine and an AI agent"),
    ("audit", "Scorecard", "17 checks across search, AI answers, agents, social and speed"),
    ("brand", "Brand read", "Muse Spark reads the screenshots, photos and pages"),
    ("paint", "Paint job", "Spark shortlists looks from your tags; Muse Wonder sketches your homepage in each"),
    ("studio", "Photo studio", "SAM 3.1 isolates each product; Muse Image reshoots it; SAM checks it"),
    ("logo", "Logo", "Spark reads your logo's idea; Muse Image redraws it; Spark checks it still reads as you"),
    ("site", "The build", "Spark writes the copy; Muse Wonder designs and codes the site"),
    ("social", "Social kit", "Handle, bio and feed posts for every channel you picked"),
    ("campaign", "The campaign", "Spark writes your got ___? brief; Muse Image casts it, one reference locking every film shot; SAM finds every hand for Spark to check; Spark reviews the film"),
    ("remix", "Remix a hit", "Popular formats you picked, reverse engineered and rebuilt with your products"),
    ("after", "Re-inspection", "The same 17 checks on the new site"),
    ("package", "The reveal", "Report, brand skill and the download"),
]


class Job:
    def __init__(self, url: str, channels: list[str], tags: list[str], jid: str | None = None,
                 formats: list[str] | None = None):
        self.id = jid or uuid.uuid4().hex[:10]
        self.dir = JOBS / self.id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state = {"id": self.id, "url": url, "channels": channels, "tags": tags,
                      "formats": formats or [],
                      "status": "running", "error": None, "created": time.time(),
                      "stages": {k: {"label": label, "detail": detail, "state": "waiting",
                                     "seconds": None} for k, label, detail in STAGES},
                      "data": {}}
        self.save()

    @classmethod
    def load(cls, jid: str) -> "Job":
        job = cls.__new__(cls)
        job.id, job.dir = jid, JOBS / jid
        job.state = json.loads((job.dir / "job.json").read_text())
        return job

    def save(self) -> None:
        tmp = self.dir / "job.json.tmp"
        tmp.write_text(json.dumps(self.state, indent=1))
        tmp.replace(self.dir / "job.json")

    def url_of(self, path: str | Path) -> str:
        """Where the browser fetches a job file: /jobs/<id>/<relative path>."""
        return f"/jobs/{self.id}/{Path(path).resolve().relative_to(self.dir.resolve())}"

    async def stage(self, key: str, fn, *args):
        st = self.state["stages"][key]
        st["state"], t0 = "running", time.monotonic()
        self.save()
        try:
            result = await fn(*args) if asyncio.iscoroutinefunction(fn) else await asyncio.to_thread(fn, *args)
        except Exception:
            st["state"] = "failed"
            raise
        st["state"], st["seconds"] = "done", round(time.monotonic() - t0, 1)
        self.save()
        return result

    def fail(self, e: Exception) -> None:
        self.state["status"], self.state["error"] = "error", f"{type(e).__name__}: {e}"
        traceback.print_exc()
        self.save()

    # --- act one ----------------------------------------------------------------

    async def act_one(self) -> None:
        d = self.state["data"]
        try:
            s: Site = await self.stage("inspect", inspect, self.state["url"], self.dir)
            d["before"] = {"desktop": self.url_of(s.shots["desktop"]), "phone": self.url_of(s.shots["phone"]),
                           "name": s.name_guess, "url": s.final_url}
            checks = await self.stage("audit", audit.run, s)
            d["audit_before"] = {"score": audit.score(checks), "checks": audit.as_dicts(checks)}

            def read() -> dict:
                ph = brand.download_photos(s, self.dir / "src")
                prof = brand.read_brand(s, ph)
                prof["socials"] = s.socials
                prof["_photos"] = [asdict(p) for p in ph]
                return prof
            prof = await self.stage("brand", read)
            (self.dir / "brand.json").write_text(json.dumps(prof, indent=1))
            d["brand"] = {k: prof[k] for k in ("name", "one_liner", "category", "audience", "location",
                                               "voice", "products", "gaps", "proof")}

            def paint() -> list[dict]:
                # Shortlist from the tags, then sketch their homepage in every look, so the
                # owner chooses from their own site, not from a description.
                rng = random.Random()
                cards = directions.pick(prof, self.state["tags"], rng)
                picks = mockups.leads(cards, prof, rng)
                photos = {p["index"]: Path(p["path"]) for p in prof["_photos"]}
                with ThreadPoolExecutor(max_workers=2) as pool:
                    copy_f = pool.submit(site.write_copy, prof)
                    prev_f = pool.submit(directions.previews, cards,
                                         [[(photos[x["photo"]], x["subject"]) for x in row] for row in picks],
                                         self.dir / "directions")
                    copy, outs = copy_f.result(), prev_f.result()
                (self.dir / "copy.json").write_text(json.dumps(copy, indent=1))
                for k, done in enumerate(outs):  # a lead that wouldn't reshoot hands over to the second
                    if len(done) > 1 and done[0] is None and done[1] is not None:
                        picks[k], outs[k] = picks[k][::-1], done[::-1]
                firsts = [row[0] if row else None for row in picks]
                for c, v, row, done in zip(cards, mockups.variants(cards, firsts, copy, rng), picks, outs):
                    c["variant"] = v
                    c["reshoots"] = [{"product": x["name"], "path": str(o) if o else None} for x, o in zip(row, done)]
                    lead = done[0] if done else None
                    c["preview_path"] = str(lead) if lead else None
                    c["preview"] = self.url_of(lead) if lead else None
                for c, sk in zip(cards, mockups.sketches(cards, prof, copy, self.dir / "directions")):
                    c["sketch"] = sk
                    if sk:
                        c["sketch_url"] = self.url_of(Path(sk["desktop"]))
                        c["sketch_phone"] = self.url_of(Path(sk["phone"]))
                        c["sketch_page"] = self.url_of(Path(sk["html"]))
                return cards
            cards = await self.stage("paint", paint)
            (self.dir / "cards.json").write_text(json.dumps(cards, indent=1))
            # The browser gets the cards without local file paths; the build reads cards.json.
            d["cards"] = [{k: v for k, v in c.items() if k not in ("sketch", "preview_path", "reshoots")} for c in cards]
            self.state["status"] = "choose"
            self.save()
        except Exception as e:
            self.fail(e)

    # --- act two ----------------------------------------------------------------

    async def act_two(self, direction_id: str, self_base: str) -> None:
        d = self.state["data"]
        try:
            self.state["status"], d["direction"] = "building", direction_id
            self.save()
            prof = json.loads((self.dir / "brand.json").read_text())
            cards = json.loads((self.dir / "cards.json").read_text())
            direction = next(c for c in cards if c["id"] == direction_id)
            site_before = Site.from_json((self.dir / "site.json").read_text())
            pics = {p["index"]: Path(p["path"]) for p in prof["_photos"]}

            shots = await self.stage("studio", photos.studio, prof["products"], pics, direction,
                                     self.dir / "studio")
            if not shots:
                raise RuntimeError("No product photos to work with on this site.")
            d["shots"] = [{**asdict(x), "landscape_url": self.url_of(x.landscape),
                           "portrait_url": self.url_of(x.portrait), "source_url": self.url_of(x.source),
                           "detail_url": self.url_of(x.detail) if x.detail else None}
                          for x in shots]

            mark = await self.stage("logo", logo.remake, site_before.logo, prof, direction,
                                    self.dir / "logo")
            d["logo"] = {"original": self.url_of(mark["original"]) if mark["original"] else None,
                         "mark": self.url_of(mark["mark"]) if mark["mark"] else None,
                         "motif": mark.get("motif"), "note": mark["note"]}
            mark = mark if mark["mark"] else None

            # Build what they chose: the sketch's copy, headline and lead product.
            copy = json.loads((self.dir / "copy.json").read_text()) if (self.dir / "copy.json").exists() else None
            v = direction.get("variant") or {}
            if copy and v.get("headline"):
                copy["h1"] = v["headline"]
            lead = [x for x in shots if x.product == v.get("hero_product")]
            site_shots = lead + [x for x in shots if x not in lead]
            approved = {**direction["sketch"], "variant": v} if direction.get("sketch") else None
            built = await self.stage("site", site.build, prof, direction, site_shots,
                                     site_before.final_url, self.dir / "site", mark, copy, approved)
            d["site"] = {"url": f"/jobs/{self.id}/site/index.html", "copy": built["copy"],
                         "fidelity": built.get("fidelity")}

            channels = self.state["channels"]

            def kit() -> dict:
                plan = social.plan(prof, shots, channels or ["instagram"])
                return social.compose(plan, shots, direction, prof["name"], self.dir / "social")
            plan = await self.stage("social", kit)
            (self.dir / "social.json").write_text(json.dumps(plan, indent=1))
            for ch in plan["channels"]:
                for p in ch["posts"]:
                    if p.get("image"):
                        p["image_url"] = self.url_of(p["image"])
            d["social"] = plan

            camp = await self.stage("campaign", campaign.make, prof, shots, direction, self.dir / "campaign",
                                    prof["contact"].get("order_url") or site_before.final_url)
            d["campaign"] = {
                **{k: camp[k] for k in ("question", "thesis", "gate", "hashtags")},
                "pieces": [{**{k: v for k, v in p.items() if k not in ("image", "raw")},
                            "image": self.url_of(p["image"]), "raw": self.url_of(p["raw"])} for p in camp["pieces"]],
                "film": {**{k: v for k, v in camp["film"].items() if k not in ("mp4", "poster", "cast", "beats")},
                         "mp4": self.url_of(camp["film"]["mp4"]), "poster": self.url_of(camp["film"]["poster"]),
                         "cast": self.url_of(camp["film"]["cast"]),
                         "beats": [{**b, "image": self.url_of(b["image"])} for b in camp["film"]["beats"]]},
            }

            remixes = None
            if self.state.get("formats"):  # only when the owner picked or uploaded a format
                remixes = await self.stage("remix", remix.make, prof, shots, direction, mark,
                                           self.dir / "remix", self.state.get("formats"))
                d["remixes"] = [{
                    "title": r["best"]["grounded"]["title"], "format": r["format"],
                    "mp4": self.url_of(r["best"]["render"]["mp4"]),
                    "poster": self.url_of(r["best"]["render"]["poster"]),
                    "review": r["best"]["review"], "grounded": r["best"]["grounded"],
                    "timeline": r["best"]["render"]["timeline"],
                    "cuts": [c["review"]["overall"] for c in r["cuts"]],
                    "angles": [{**a, "image": self.url_of(a["image"])} for a in r["angles"]],
                } for r in remixes]
            else:
                self.state["stages"]["remix"]["state"] = "skipped"

            async def after():
                s2 = await inspect(f"{self_base}/jobs/{self.id}/site/index.html", self.dir / "after",
                                   trusted=True, follow=False)
                return s2, audit.run(s2)
            s2, checks_after = await self.stage("after", after)
            # The new site is served from a preview address here; on the real domain the
            # canonical and sitemap point home, so judge those two on what we wrote.
            for c in checks_after:
                if c.id == "canonical":
                    c.passed = bool(s2.signals.get("canonical"))
            d["audit_after"] = {"score": audit.score(checks_after), "checks": audit.as_dicts(checks_after),
                                "desktop": self.url_of(s2.shots["desktop"]), "phone": self.url_of(s2.shots["phone"])}

            def package() -> dict:
                checks_before = audit.run(site_before)
                folder = skill.write(prof, direction, plan, built["base"], self.dir, remixes, mark, camp)
                files = {"site": "site/", "skill": folder.name + "/", "perf_after": s2.perf}
                r = report.build(site_before, checks_before, checks_after, prof, direction,
                                 [asdict(x) for x in shots], plan, remixes, files, d.get("logo"), camp)
                report.write(r, self.dir)
                zip_path = self.make_zip(folder)
                return {"report": self.url_of(self.dir / "report.html"),
                        "skill": self.url_of(folder / "SKILL.md"),
                        "skill_md": (folder / "SKILL.md").read_text(),
                        "zip": self.url_of(zip_path), "value": r["value"],
                        "fixed": r["fixed"], "agent_ready": r["agent_ready"]}
            d["package"] = await self.stage("package", package)
            self.state["status"] = "done"
            self.save()
        except Exception as e:
            self.fail(e)

    def make_zip(self, skill_folder: Path) -> Path:
        stage = self.dir / "package"
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir()
        shutil.copytree(self.dir / "site", stage / "website")
        shutil.copytree(skill_folder, stage / skill_folder.name)
        (stage / "social").mkdir()
        for f in (self.dir / "social").glob("*.jpg"):
            shutil.copy(f, stage / "social" / f.name)
        captions = []
        plan = json.loads((self.dir / "social.json").read_text())
        for ch in plan["channels"]:
            for k, p in enumerate(ch["posts"]):
                captions += [f"## {ch['channel']} {k + 1}", "", p["caption"], "", f"Alt text: {p['alt']}", ""]
        (stage / "social" / "captions.md").write_text("\n".join(captions))
        camp_dir = self.dir / "campaign"
        if (camp_dir / "campaign.json").exists():
            camp = json.loads((camp_dir / "campaign.json").read_text())
            (stage / "campaign").mkdir()
            notes = [f"# {camp['question']}", "", f"{camp['thesis']['not_x']} {camp['thesis']['is_y']}", ""]
            for k, p in enumerate(camp["pieces"]):
                name = f"{k + 1}-{p['kind']}.jpg"
                shutil.copy(p["image"], stage / "campaign" / name)
                notes += [f"## {name}", "", p["caption"], "", " ".join(camp["hashtags"]), ""]
            f = camp["film"]
            shutil.copy(f["mp4"], stage / "campaign" / "film.mp4")
            notes += ["## film.mp4", "", f["caption"], "", " ".join(camp["hashtags"]), "",
                      f"Sound: pick {f['sound']} in the app.", ""]
            (stage / "campaign" / "captions.md").write_text("\n".join(notes))
        rem = self.state["data"].get("remixes") or []
        if rem:
            (stage / "video").mkdir()
            notes = []
            for k, r in enumerate(rem):
                src = self.dir / r["mp4"].split(f"/jobs/{self.id}/", 1)[-1]
                if src.exists():
                    shutil.copy(src, stage / "video" / f"{k + 1}-{r['format']['id']}.mp4")
                g = r["grounded"]
                notes += [f"## {k + 1}. {g['title']} ({r['format']['name']})", "",
                          f"Format: {r['format']['essence']}", "", g["caption"], "",
                          " ".join(g["hashtags"]), "", f"Sound: pick {g['sound']} in the app.", ""]
            (stage / "video" / "captions.md").write_text("\n".join(notes))
        logo_dir = self.dir / "logo"
        if (logo_dir / "mark.png").exists():
            (stage / "logo").mkdir()
            for f in ("mark.png", "mark_light.png", "original.png"):
                if (logo_dir / f).exists():
                    shutil.copy(logo_dir / f, stage / "logo" / f)
        (stage / "photos").mkdir()
        for f in (self.dir / "studio").glob("*_landscape.png"):
            shutil.copy(f, stage / "photos" / f.name)
        for f in (self.dir / "studio").glob("*_portrait.png"):
            shutil.copy(f, stage / "photos" / f.name)
        for f in (self.dir / "studio").glob("*_detail.png"):
            shutil.copy(f, stage / "photos" / f.name)
        shutil.copy(self.dir / "report.html", stage / "report.html")
        archive = shutil.make_archive(str(self.dir / "pimp-my-social-kit"), "zip", stage)
        return Path(archive)
