#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从蓝奏云解析接口获取 JSON，下载其中的 zip 并解压到 data 文件夹。

用法:
    python lanzou_download.py
    python lanzou_download.py --share-url https://eassos.lanzoue.com/DG64Lite
    python lanzou_download.py --api-base https://api.ruseo.cn/api/lanzou_parse --out-dir data
"""

import argparse
import io
import os
import sys
import zipfile
import urllib.parse
from pathlib import Path

import requests

# 默认配置
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
    """调用解析接口，返回 JSON。"""
    # 把分享链接作为 url 参数拼到接口地址上
    resp = requests.get(
        api_base,
        params={"url": share_url},
        headers=HEADERS,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def extract_download_info(payload: dict) -> tuple[str, str]:
    """
    从 JSON 中取出 (下载直链, 文件名)。
    结构参考 resp.json: {"data": {"name": "xxx.zip", "downurl": "http..."}}
    做了几层兼容，缺失字段时用默认名。
    """
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    downurl = data.get("downurl") or data.get("url") or data.get("durl")
    if not downurl:
        raise RuntimeError(
            "未在返回 JSON 中找到下载链接(downurl)，请检查接口返回或 share-url 是否有效。"
        )
    name = data.get("name") or "download.zip"
    return downurl, name


def download_file(url: str, dest_path: Path, timeout: int = 60, chunk_size: int = 1 << 16) -> None:
    """流式下载文件到 dest_path，并打印进度。"""
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
                    sys.stdout.write(f"\r下载中... {done}/{total} bytes ({pct}%)")
                else:
                    sys.stdout.write(f"\r下载中... {done} bytes")
                sys.stdout.flush()
    sys.stdout.write("\n")


def unzip_to(zip_path: Path, out_dir: Path) -> None:
    """解压 zip 到 out_dir。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        # 过滤潜在的非法路径（zip slip 防护）
        for info in zf.infolist():
            target = (out_dir / info.filename).resolve()
            if not str(target).startswith(str(out_dir.resolve())):
                raise RuntimeError(f"压缩包内含非法路径，已中止: {info.filename}")
        zf.extractall(out_dir)


def main():
    parser = argparse.ArgumentParser(description="蓝奏云解析下载并解压脚本")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="解析接口地址")
    parser.add_argument("--share-url", default=DEFAULT_SHARE_URL, help="蓝奏云分享链接")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="下载与解压目标文件夹")
    parser.add_argument("--keep-zip", action="store_true", help="解压后保留原始 zip 文件")
    parser.add_argument("--no-unzip", action="store_true", help="只下载不解压")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] 请求解析接口: {args.api_base}?url={args.share_url}")
    payload = get_json(args.api_base, args.share_url)

    # 接口可能有外层 code 包裹，简单提示
    if isinstance(payload, dict) and payload.get("code") not in (None, 0, 200):
        print(f"  接口返回 code={payload.get('code')}, msg={payload.get('msg')}")

    downurl, filename = extract_download_info(payload)
    print(f"[2/3] 获取到文件: {filename}")
    print(f"      直链: {downurl}")

    zip_path = out_dir / filename
    download_file(downurl, zip_path)
    print(f"      已保存到: {zip_path}")

    if args.no_unzip:
        print("[3/3] 已跳过解压 (--no-unzip)。")
        return

    print(f"[3/3] 解压到: {out_dir}")
    unzip_to(zip_path, out_dir)
    if not args.keep_zip:
        zip_path.unlink()
        print(f"      已删除临时 zip: {zip_path}")
    print("完成。")


if __name__ == "__main__":
    main()
