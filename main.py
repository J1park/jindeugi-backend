from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from datetime import datetime

app = FastAPI(title="진드기 CREW API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MEMBERS = [
    {"name": "진호",   "soopId": "jangjh5409"},
    {"name": "뽀끔",   "soopId": "fishstory"},
    {"name": "이루희", "soopId": "mingkymya"},
    {"name": "호냥이", "soopId": "yaya1787"},
    {"name": "오늘님", "soopId": "pqf1234"},
    {"name": "찌미",   "soopId": "zzimio3o"},
    {"name": "히키",   "soopId": "hikicomoring"},
    {"name": "설빈달", "soopId": "nsnowthemoon"},
    {"name": "찰리씨", "soopId": "sircharlee"},
    {"name": "야구자", "soopId": "yaguja00"},
    {"name": "니즈",   "soopId": "neez0611"},
    {"name": "두칠",   "soopId": "hwyjump"},
]

SOOP_BASE = "https://api-channel.sooplive.com/v1.1/channel"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer": "https://www.sooplive.com/",
    "Origin": "https://www.sooplive.com",
}

async def fetch_station(client: httpx.AsyncClient, soop_id: str) -> dict:
    try:
        r = await client.get(
            f"{SOOP_BASE}/{soop_id}/station",
            headers=HEADERS,
            timeout=8
        )

        if r.status_code == 200:
            body = r.json()
            return body.get("data", body)

    except Exception as e:
        print(e)

    return {}

async def fetch_posts_try(client: httpx.AsyncClient, soop_id: str, per_page: int = 5) -> list:
    try:
        r = await client.get(
            f"{SOOP_BASE}/{soop_id}/home/section/post",
            headers=HEADERS,
            timeout=10
        )

        if r.status_code == 200:
            body = r.json()

            if isinstance(body, dict):
                if "data" in body:
                    data = body["data"]

                    if isinstance(data, list):
                        return data[:per_page]

                    if isinstance(data, dict):
                        return (
                            data.get("list")
                            or data.get("posts")
                            or data.get("items")
                            or []
                        )

    except Exception as e:
        print("POST ERROR:", e)

    return []

def build_live_result(member: dict, station_data: dict) -> dict:

    station = station_data.get("station", {})

    is_live = bool(station.get("broadStart"))

    return {
        "name": member["name"],
        "soopId": member["soopId"],
        "isLive": is_live,
        "embedUrl": f"https://play.sooplive.com/{member['soopId']}/embeded" if is_live else None,

        "title": station.get("stationTitle", ""),

        "viewers": station.get(
            "currentViewCnt",
            station.get("totalViewCnt", 0)
        ),

        "thumbnail": station.get("profileImage", ""),

        "broadNo": str(
            station.get("stationNo", "")
        ),

        "upCount": 0
    }

def build_post_result(member: dict, raw: dict) -> dict:
    post_id = raw.get("title_no", raw.get("post_no", raw.get("id", "")))

    return {
        "member": member["name"],
        "soopId": member["soopId"],
        "platform": "soop",
        "postId": str(post_id),
        "title": raw.get("title_name", raw.get("title", "")),
        "content": raw.get("contents", raw.get("content", "")),
        "date": raw.get("reg_date", raw.get("created_at", "")),
        "upCount": raw.get("up_cnt", raw.get("up_count", 0)),
        "viewCount": raw.get("read_cnt", raw.get("view_cnt", 0)),
        "thumbnail": raw.get("thumb", raw.get("thumbnail", raw.get("broad_img", ""))),
        "url": f"https://www.sooplive.com/{member['soopId']}/post/{post_id}",
    }

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "진드기 CREW API",
        "version": "1.3",
        "updatedAt": datetime.now().isoformat(),
    }

@app.get("/api/live")
async def get_all_live():
    async with httpx.AsyncClient() as client:
        stations = await asyncio.gather(*[
            fetch_station(client, m["soopId"]) for m in MEMBERS
        ])

    results = [build_live_result(m, s) for m, s in zip(MEMBERS, stations)]
    live = [r for r in results if r["isLive"]]

    return {
        "updatedAt": datetime.now().isoformat(),
        "liveCount": len(live),
        "members": results,
    }

@app.get("/api/live/{soop_id}")
async def get_live(soop_id: str):
    member = next((m for m in MEMBERS if m["soopId"] == soop_id), None)
    if not member:
        member = {"name": soop_id, "soopId": soop_id}

    async with httpx.AsyncClient() as client:
        station = await fetch_station(client, soop_id)

    return build_live_result(member, station)

@app.get("/api/posts")
async def get_all_posts(per_page: int = Query(5, ge=1, le=20)):
    async with httpx.AsyncClient() as client:
        raw_lists = await asyncio.gather(*[
            fetch_posts_try(client, m["soopId"], per_page) for m in MEMBERS
        ])

    all_posts = []
    for member, raw_list in zip(MEMBERS, raw_lists):
        for raw in raw_list:
            all_posts.append(build_post_result(member, raw))

    all_posts.sort(key=lambda x: x.get("date", ""), reverse=True)

    return {
        "updatedAt": datetime.now().isoformat(),
        "total": len(all_posts),
        "posts": all_posts[:50],
    }

@app.get("/api/posts/{soop_id}")
async def get_member_posts(soop_id: str, per_page: int = Query(10, ge=1, le=20)):
    member = next((m for m in MEMBERS if m["soopId"] == soop_id), None)
    if not member:
        member = {"name": soop_id, "soopId": soop_id}

    async with httpx.AsyncClient() as client:
        raw_list = await fetch_posts_try(client, soop_id, per_page)

    return {
        "member": member["name"],
        "posts": [build_post_result(member, r) for r in raw_list],
    }

@app.get("/api/members")
async def get_members():
    return {"members": MEMBERS}

@app.get("/api/debug/{soop_id}")
async def debug_api(soop_id: str):
    out = {}

    async with httpx.AsyncClient() as client:
        for label, url, params in [
            ("station", f"{SOOP_BASE}/{soop_id}/station", {}),
            ("post", f"{SOOP_BASE}/{soop_id}/home/section/post", {}),
        ]:
            try:
                r = await client.get(url, headers=HEADERS, params=params, timeout=8)
                text = r.text

                try:
                    body = r.json()
                    data = body.get("data", [])
                    data_count = len(data) if isinstance(data, list) else ("dict" if isinstance(data, dict) else 0)
                except Exception:
                    data_count = 0

                out[label] = {
                    "url": str(r.url),
                    "status": r.status_code,
                    "dataCount": data_count,
                    "sample": text[:3000],
                }
            except Exception as e:
                out[label] = {"error": str(e)}

    return {
        "soopId": soop_id,
        "results": out,
    }

@app.get("/api/test/{soop_id}")
async def test_station(soop_id: str):
    async with httpx.AsyncClient() as client:
        data = await fetch_station(client, soop_id)

    return data
