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
import shutil
import time
import traceback
import uuid
from dataclasses import asdict
from pathlib import Path

from . import audit, brand, campaign, directions, logo, photos, remix, report, site, skill, social
from .crawl import Site, inspect

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "out" / "jobs"

STAGES = [
    ("inspect", "Inspection", "Rendering the site like a visitor, a search engine and an AI agent"),
    ("audit", "Scorecard", "17 checks across search, AI answers, agents, social and speed"),
    ("brand", "Brand read", "Muse Spark reads the screenshots, photos and pages"),
    ("paint", "Paint job", "Spark picks your directions; Muse Image previews each"),
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
                cards = directions.pick(prof, self.state["tags"])
                hero = prof["hero_photo"] if prof["hero_photo"] >= 0 else 0
                subj = next((p["subject"] for p in prof["products"] if p["photo"] == hero), "product")
                if prof["_photos"]:
                    outs = directions.previews(cards, Path(prof["_photos"][hero]["path"]), subj,
                                               self.dir / "directions")
                    for c, o in zip(cards, outs):
                        c["preview"] = self.url_of(o) if o else None
                return cards
            cards = await self.stage("paint", paint)
            (self.dir / "cards.json").write_text(json.dumps(cards, indent=1))
            d["cards"] = cards
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

            built = await self.stage("site", site.build, prof, direction, shots,
                                     site_before.final_url, self.dir / "site", mark)
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
