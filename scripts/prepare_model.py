#!/usr/bin/env python3
"""Install SHA-256 pinned free/local inference artifacts; never accepts agreements."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import os
import secrets
import subprocess
import tarfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'b4243c156154b6dca9324415f8c7ccc098b4aed1'
MODEL_NAME = 'gemma-4-E2B-it-Q4_0.gguf'
MODEL_SHA = '8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52'
MODEL_SIZE = 2841481184
RUNTIME_TAG = 'b11583'
RUNTIME_SHA = 'd23832f4b847a722a64c9bf57e518c3df81dfab325942182ff17792d5d33351f'
MODEL_URL = f'https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF/resolve/{REVISION}/{MODEL_NAME}'
RUNTIME_URL = f'https://github.com/ggml-org/llama.cpp/releases/download/{RUNTIME_TAG}/llama-{RUNTIME_TAG}-bin-macos-arm64.tar.gz'
SOURCE_COMMIT = '98801578818b26d833a1fe244870d64b0c34bb46'
SOURCE_SHA = 'a4e86435bd4983030d3cf85a3475e2e9aea6794d94f047f1a3993333a8734fbf'
SOURCE_URL = f'https://codeload.github.com/ggml-org/llama.cpp/tar.gz/{SOURCE_COMMIT}'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def download_ranges(url, destination, size, expected, workers=8):
    if destination.exists() and destination.stat().st_size == size and sha(destination) == expected:
        return
    parts = destination.parent / (destination.name + '.parts')
    parts.mkdir(exist_ok=True)
    chunk = (size + workers - 1) // workers
    def get(index):
        start, end = index * chunk, min(size, (index + 1) * chunk) - 1
        target = parts / str(index)
        if target.exists() and target.stat().st_size == end - start + 1:
            return target
        for attempt in range(128):
            try:
                offset = target.stat().st_size if target.exists() else 0
                if offset == end - start + 1:
                    return target
                resume_start = start + offset
                request_end = min(end, resume_start + 32 * 1024 * 1024 - 1)
                request = urllib.request.Request(url, headers={'Range': f'bytes={resume_start}-{request_end}'})
                with urllib.request.urlopen(request, timeout=20) as response:
                    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {resume_start}-{request_end}/{size}':
                        raise RuntimeError('Source did not honor the exact bounded byte range.')
                    with target.open('ab') as handle:
                        while block := response.read(64 * 1024):
                            handle.write(block)
                if target.stat().st_size < end - start + 1:
                    continue
                if target.stat().st_size != end - start + 1:
                    raise RuntimeError('Oversized download segment')
                print(f'Model segment {index + 1}/{workers} complete', flush=True)
                return target
            except Exception:
                if attempt == 127:
                    raise
                time.sleep(2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        completed = list(pool.map(get, range(workers)))
    temporary = destination.with_suffix('.partial')
    with temporary.open('wb') as output:
        for part in completed:
            with part.open('rb') as source:
                while block := source.read(8 * 1024 * 1024):
                    output.write(block)
    if sha(temporary) != expected:
        temporary.unlink()
        for part in completed:
            part.unlink()
        parts.rmdir()
        raise RuntimeError('Model SHA-256 mismatch; unverified segments removed. Retry setup; no artifact was activated.')
    temporary.replace(destination)
    for part in completed:
        part.unlink()
    parts.rmdir()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', action='store_true', help='Start foreground loopback model server after verification')
    args = parser.parse_args()
    if os.uname().machine != 'arm64' or os.uname().sysname != 'Darwin':
        raise SystemExit('This pinned runtime is macOS ARM64 only.')
    model_dir, runtime_dir = ROOT / '.model', ROOT / '.runtime'
    model_dir.mkdir(exist_ok=True)
    runtime_dir.mkdir(exist_ok=True)
    archive = runtime_dir / f'llama-{RUNTIME_TAG}.tar.gz'
    runtime_build = 'official-release'
    cached_source = runtime_dir / 'llama-source.tar.gz'
    source_available = cached_source.is_file() and sha(cached_source) == SOURCE_SHA
    if (not archive.exists() or sha(archive) != RUNTIME_SHA) and not source_available:
        try:
            subprocess.run(['curl', '--fail', '--location', '--max-time', '30', '--output', str(archive), RUNTIME_URL], check=True)
        except subprocess.CalledProcessError:
            runtime_build = 'source-build'
    if archive.exists() and sha(archive) == RUNTIME_SHA:
        extracted = runtime_dir / RUNTIME_TAG
        if not extracted.exists():
            extracted.mkdir()
            with tarfile.open(archive) as bundle:
                bundle.extractall(extracted, filter='data')
        with tarfile.open(archive) as bundle:
            for member in bundle.getmembers():
                if member.isfile():
                    expected = hashlib.sha256(bundle.extractfile(member).read()).hexdigest()
                    actual_path = extracted / member.name
                    if not actual_path.is_file() or sha(actual_path) != expected:
                        raise SystemExit('Extracted runtime bytes differ from the pinned archive; reinstall the generated runtime directory.')
        binaries = list(extracted.rglob('llama-server'))
        if len(binaries) != 1:
            raise SystemExit('Pinned archive must contain one llama-server.')
        server = binaries[0]
    else:
        runtime_build = 'source-build'
        source_archive = runtime_dir / 'llama-source.tar.gz'
        if not source_archive.exists() or sha(source_archive) != SOURCE_SHA:
            subprocess.run(['curl', '--fail', '--location', '--max-time', '120', '--output', str(source_archive), SOURCE_URL], check=True)
        if sha(source_archive) != SOURCE_SHA:
            raise SystemExit('Runtime source SHA-256 mismatch.')
        source_parent = runtime_dir / 'source'
        if not source_parent.exists():
            source_parent.mkdir()
            with tarfile.open(source_archive) as bundle:
                bundle.extractall(source_parent, filter='data')
        source = source_parent / ('llama.cpp-' + SOURCE_COMMIT)
        with tarfile.open(source_archive) as bundle:
            for member in bundle.getmembers():
                if member.isfile():
                    expected = hashlib.sha256(bundle.extractfile(member).read()).hexdigest()
                    actual_path = source_parent / member.name
                    if not actual_path.is_file() or sha(actual_path) != expected:
                        raise SystemExit('Extracted runtime source differs from the pinned archive; reinstall the generated source directory.')
        cmake = runtime_dir / 'build-tools/cmake/data/bin/cmake'
        if not cmake.is_file():
            raise SystemExit('Install isolated free build tool first: uv pip install --target .runtime/build-tools cmake==4.1.2')
        build = runtime_dir / 'build'
        subprocess.run([str(cmake), '-S', str(source), '-B', str(build), '-DCMAKE_BUILD_TYPE=Release', '-DGGML_METAL=ON', '-DLLAMA_BUILD_TESTS=OFF', '-DLLAMA_BUILD_EXAMPLES=OFF'], check=True)
        subprocess.run([str(cmake), '--build', str(build), '--target', 'llama-server', '-j', '4'], check=True)
        server = build / 'bin/llama-server'
    server.chmod(server.stat().st_mode | 0o100)
    download_ranges(MODEL_URL, model_dir / MODEL_NAME, MODEL_SIZE, MODEL_SHA)
    manifest = {
        'model': 'google/gemma-4-E2B-it', 'source_revision': '3e22461f65e89153144f8adb70e3b8c2cc9845a7',
        'conversion_source_revisions': {'PRIMARY': '3e22461f65e89153144f8adb70e3b8c2cc9845a7', 'ASSISTANT': '2d874ef7d29f9a30599a1e4b3c1cbc9595f005df', 'QAT_Q4_0': 'ebc7e1a211354561464cb82ed6d886792138dcb6', 'QAT_Q4_0_UNQUANTIZED': '6befbaca7398925921802abd1f277b495b78b738'},
        'artifact_repository': 'ggml-org/gemma-4-E2B-it-GGUF', 'artifact_revision': REVISION,
        'artifact': MODEL_NAME, 'quantization': 'Q4_0', 'model_sha256': MODEL_SHA,
        'model_bytes': MODEL_SIZE, 'license': 'Apache-2.0',
        'runtime_repository': 'ggml-org/llama.cpp', 'runtime_tag': RUNTIME_TAG,
        'runtime_commit': '98801578818b26d833a1fe244870d64b0c34bb46',
        'runtime_server_sha256': sha(server), 'runtime_build': runtime_build, 'runtime_archive_sha256': RUNTIME_SHA if runtime_build == 'official-release' else None,
        'runtime_source_sha256': SOURCE_SHA if runtime_build == 'source-build' else None,
        'runtime_build_flags': ['Release', 'GGML_METAL=ON', 'LLAMA_BUILD_TESTS=OFF', 'LLAMA_BUILD_EXAMPLES=OFF'] if runtime_build == 'source-build' else [],
        'platform': 'macOS-arm64',
        'alias': 'handoffready-gemma4-e2b', 'context_tokens': 8192,
        'model_url': MODEL_URL, 'runtime_url': RUNTIME_URL,
    }
    key_file = model_dir / 'server.key'
    if not key_file.exists():
        descriptor = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(secrets.token_urlsafe(32) + '\n')
    key_file.chmod(0o600)
    (model_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2), flush=True)
    if args.start:
        os.execv(str(server), [str(server), '-m', str(model_dir / MODEL_NAME), '--alias', 'handoffready-gemma4-e2b', '--host', '127.0.0.1', '--port', '18081', '-c', '8192', '-np', '1', '-ngl', '99', '--jinja', '--no-webui', '--reasoning', 'off', '--api-key-file', str(key_file), '--cors-origins', 'http://127.0.0.1:8877'])


if __name__ == '__main__':
    main()
