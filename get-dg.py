

import argparse
import io
import os
import sys
import zipfile
import urllib.parse
from pathlib import Path

import requests

DEFAULT_API_BASE = "https://api.ruseo.cn/api/lanzou_parse"
DEFAULT_SHARE_URL = "https://eassos.lanzoue.com/DG64Lite"
DEFAULT_OUT_DIR = "data"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def get_json(api_base: str, share_url: str, timeout: int = 30) -> dict:
    resp = requests.get(
        api_base,
        params={"url": share_url},
        headers=HEADERS,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def extract_download_info(payload: dict) -> tuple[str, str]:
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    downurl = data.get("downurl") or data.get("url") or data.get("durl")
    if not downurl:
        raise RuntimeError(
            "didn't find url!"
        )
    name = data.get("name") or "download.zip"
    return downurl, name


def download_file(url: str, dest_path: Path, timeout: int = 60, chunk_size: int = 1 << 16) -> None:
    with requests.get(url, headers=HEADERS, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done * 100 // total
                    sys.stdout.write(f"\rDownloading... {done}/{total} bytes ({pct}%)")
                else:
                    sys.stdout.write(f"\rDownloading... {done} bytes")
                sys.stdout.flush()
    sys.stdout.write("\n")


def unzip_to(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            target = (out_dir / info.filename).resolve()
            if not str(target).startswith(str(out_dir.resolve())):
                raise RuntimeError(f"path error! {info.filename}")
        zf.extractall(out_dir)


def main():
    parser = argparse.ArgumentParser(description="download unzip script")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="api link")
    parser.add_argument("--share-url", default=DEFAULT_SHARE_URL, help="file link")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="target dir")
    parser.add_argument("--keep-zip", action="store_true", help="keep zip")
    parser.add_argument("--no-unzip", action="store_true", help="only download")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] request: {args.api_base}?url={args.share_url}")
    payload = get_json(args.api_base, args.share_url)

    # 接口可能有外层 code 包裹，简单提示
    if isinstance(payload, dict) and payload.get("code") not in (None, 0, 200):
        print(f"  return code={payload.get('code')}, msg={payload.get('msg')}")

    downurl, filename = extract_download_info(payload)
    print(f"[2/3] get file: {filename}")
    print(f"      link: {downurl}")

    zip_path = out_dir / filename
    download_file(downurl, zip_path)
    print(f"      saved: {zip_path}")

    if args.no_unzip:
        print("[3/3] skip unpack (--no-unzip)。")
        return

    print(f"[3/3] unpack to: {out_dir}")
    unzip_to(zip_path, out_dir)
    if not args.keep_zip:
        zip_path.unlink()
        print(f"      delate temp file: {zip_path}")
    print("complety")


if __name__ == "__main__":
    main()
