#!/usr/bin/env python3
"""GitHub 新 Release → 蓝奏云 → 站点链接。

由 .github/workflows/sync-release.yml 调用：
1. 读取 Ckxkx/account-atlas 最新 Release；
2. 与 .github/release-state.json 比较，没有新版本（且链接已存在）就退出；
3. 下载 Atlas.apk / Atlas.ipa，清掉蓝奏云文件夹里的旧安装包，上传新包，取分享链接；
4. 改写页面里 data-dl / data-size / data-ver / data-host 标记和 README 下载段落；
5. 写回状态文件，并通过 GITHUB_OUTPUT 告诉工作流是否有改动。

蓝奏云没有官方 API，这里用的是网页端接口（pc.woozooo.com），登录靠 Cookie。
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import functools
import requests

print = functools.partial(print, flush=True)  # noqa: A001  实时输出日志

REPO = os.environ.get("ATLAS_REPO", "Ckxkx/account-atlas")
ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".github" / "release-state.json"
PAGES = ["index.html", "guide/index.html", "sidestore/index.html", "faq/index.html"]
ASSETS = {"apk": "Atlas.apk", "ipa": "Atlas.ipa"}
FORCE = os.environ.get("FORCE", "").lower() in ("1", "true", "yes")

LZ = "https://pc.woozooo.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def out(key, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"{key}={value}\n")
    print(f"{key}={value}")


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


# ---------------- GitHub ----------------
def latest_release():
    headers = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GH_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    r = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest", headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def download(url, dest):
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    return dest.stat().st_size


# ---------------- 蓝奏云 ----------------
class Lanzou:
    def __init__(self, ylogin, phpdisk_info):
        self.uid = ylogin
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Referer": f"{LZ}/mydisk.php",
                               "Accept-Language": "zh-CN,zh;q=0.9"})
        self.s.cookies.set("ylogin", ylogin, domain=".woozooo.com")
        self.s.cookies.set("phpdisk_info", phpdisk_info, domain=".woozooo.com")

    def check_login(self):
        try:
            res = self.api({"task": 47, "folder_id": -1})
        except Exception as e:  # noqa: BLE001
            fail(f"连接蓝奏云失败：{e}")
        if res.get("zt") == 9 or res.get("info") == "login not":
            fail("蓝奏云 Cookie 已失效：请重新登录蓝奏云，把新的 ylogin / phpdisk_info 更新到仓库 Secrets。")
        print(f"蓝奏云登录正常（zt={res.get('zt')}）")

    def api(self, data):
        r = self.s.post(f"{LZ}/doupload.php?uid={self.uid}", data=data, timeout=60)
        r.raise_for_status()
        return r.json()

    def folders(self, parent=-1):
        return self.api({"task": 47, "folder_id": parent}).get("text") or []

    def ensure_folder(self, name="Atlas"):
        fid = os.environ.get("LANZOU_FOLDER_ID", "").strip()
        if fid:
            return fid
        for f in self.folders():
            if f.get("name") == name:
                return str(f["fol_id"])
        res = self.api({"task": 2, "parent_id": -1, "folder_name": name,
                        "folder_description": "账号星图 Atlas 安装包"})
        if res.get("zt") != 1:
            fail(f"创建蓝奏云文件夹失败：{res}")
        for f in self.folders():
            if f.get("name") == name:
                return str(f["fol_id"])
        fail("创建文件夹后没找到它")

    def files(self, folder):
        out_, pg = [], 1
        while True:
            res = self.api({"task": 5, "folder_id": folder, "pg": pg})
            if not res.get("info"):
                break
            batch = res.get("text") or []
            if not isinstance(batch, list) or not batch:
                break
            out_ += batch
            if len(batch) < 18 or pg >= 20:
                break
            pg += 1
        return out_

    def delete(self, file_id):
        res = self.api({"task": 6, "file_id": file_id})
        if res.get("zt") != 1:
            print(f"::warning::删除旧文件 {file_id} 失败：{res}")

    def upload(self, path, folder):
        name = path.name
        for attempt in range(3):
            with open(path, "rb") as fh:
                r = self.s.post(f"{LZ}/html5up.php", data={
                    "task": "1", "vie": "2", "ve": "2", "id": "WU_FILE_0",
                    "folder_id_bb_n": folder, "name": name,
                }, files={"upload_file": (name, fh, "application/octet-stream")}, timeout=180)
            try:
                res = r.json()
            except ValueError:
                res = {"raw": r.text[:300]}
            if res.get("zt") == 1:
                return str(res["text"][0]["id"])
            print(f"::warning::上传 {name} 第 {attempt + 1} 次失败：{res}")
            time.sleep(10)
        fail(f"上传 {name} 到蓝奏云失败")

    def share_url(self, file_id):
        # 关闭提取码，再取分享链接
        self.api({"task": 23, "file_id": file_id, "shows": 0, "shownames": ""})
        info = self.api({"task": 22, "file_id": file_id}).get("info") or {}
        if not info.get("f_id") or info.get("f_id") == "i":
            fail(f"取分享链接失败：{info}")
        host = info["is_newd"].rstrip("/")
        if not host.startswith("http"):
            host = "https://" + host
        return f"{host}/{info['f_id']}"


# ---------------- 站点 ----------------
def fmt_size(n):
    return f"{n / 1e6:.2f} MB"


def update_site(tag, urls, sizes):
    for rel in PAGES:
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        for k in ASSETS:
            s = re.sub(rf'data-dl="{k}" href="[^"]*"', f'data-dl="{k}" href="{urls[k]}"', s)
            s = re.sub(rf'<span data-size="{k}">[^<]*</span>', f'<span data-size="{k}">{fmt_size(sizes[k])}</span>', s)
        s = re.sub(r"<span data-ver>[^<]*</span>", f"<span data-ver>{tag}</span>", s)
        s = re.sub(r"<span data-host>[^<]*</span>", "<span data-host>蓝奏云网盘</span>", s)
        p.write_text(s, encoding="utf-8")

    readme = ROOT / "README.md"
    s = readme.read_text(encoding="utf-8")
    block = ("<!-- downloads:start -->\n"
             f"- 蓝奏云网盘（{tag}）：安卓 <{urls['apk']}> · iPhone <{urls['ipa']}>\n"
             f"- GitHub Releases：<https://github.com/{REPO}/releases/latest>\n"
             "<!-- downloads:end -->")
    s = re.sub(r"<!-- downloads:start -->.*?<!-- downloads:end -->", block, s, flags=re.S)
    readme.write_text(s, encoding="utf-8")


def main():
    ylogin = os.environ.get("LANZOU_YLOGIN", "").strip()
    pinfo = os.environ.get("LANZOU_PHPDISK_INFO", "").strip()
    if not ylogin or not pinfo:
        print("::warning::未配置 LANZOU_YLOGIN / LANZOU_PHPDISK_INFO，跳过同步。")
        out("changed", "false")
        return

    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    rel = latest_release()
    tag = rel["tag_name"]
    if not FORCE and state.get("tag") == tag and state.get("apk_url") and state.get("ipa_url"):
        print(f"已是最新：{tag}")
        out("changed", "false")
        return

    assets = {a["name"]: a["browser_download_url"] for a in rel.get("assets", [])}
    missing = [n for n in ASSETS.values() if n not in assets]
    if missing:
        fail(f"{tag} 缺少安装包：{missing}")

    work = ROOT / ".release-tmp"
    work.mkdir(exist_ok=True)
    paths, sizes = {}, {}
    for k, name in ASSETS.items():
        stem, ext = name.rsplit(".", 1)
        paths[k] = work / f"{stem}-{tag}.{ext}"          # 蓝奏云里的文件名带版本号
        sizes[k] = download(assets[name], paths[k])
        print(f"下载 {name}：{sizes[k]} bytes")

    lz = Lanzou(ylogin, pinfo)
    lz.check_login()
    folder = lz.ensure_folder()
    print(f"蓝奏云文件夹 id：{folder}")

    # 先删旧安装包（只删 .apk / .ipa）
    for f in lz.files(folder):
        if f.get("name_all", "").lower().endswith((".apk", ".ipa")):
            print(f"删除旧文件：{f['name_all']}")
            lz.delete(f["id"])

    urls = {}
    for k in ASSETS:
        fid = lz.upload(paths[k], folder)
        urls[k] = lz.share_url(fid)
        print(f"{k} → {urls[k]}")

    update_site(tag, urls, sizes)
    STATE.write_text(json.dumps({"tag": tag, "apk_url": urls["apk"], "ipa_url": urls["ipa"],
                                 "apk_size": sizes["apk"], "ipa_size": sizes["ipa"],
                                 "folder_id": folder}, ensure_ascii=False, indent=2) + "\n")
    for p in paths.values():
        p.unlink(missing_ok=True)
    work.rmdir()
    out("changed", "true")
    out("tag", tag)


if __name__ == "__main__":
    main()
