#!/usr/bin/env python3
"""Configure a persistent Android release keystore from GitHub Actions secrets.

With no signing secrets present, the workflow intentionally keeps Flutter's
temporary debug signing so CI artifacts can still be built and tested.
"""

from __future__ import annotations

import base64
import binascii
import os
import re
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "source" / "android" / "app"
GRADLE_FILE = APP_DIR / "build.gradle.kts"
KEYSTORE_FILE = APP_DIR / "release-keystore.jks"
REQUIRED = (
    "ANDROID_KEYSTORE_BASE64",
    "ANDROID_KEYSTORE_PASSWORD",
    "ANDROID_KEY_ALIAS",
    "ANDROID_KEY_PASSWORD",
)


def set_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"{name}={value}\n")


def fail(message: str) -> "NoReturn":
    print(f"Android signing setup failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    values = {key: os.environ.get(key, "") for key in REQUIRED}
    supplied = [bool(value) for value in values.values()]

    if not any(supplied):
        print("No production signing secrets configured; using temporary debug signing.")
        (ROOT / "source" / "build").mkdir(parents=True, exist_ok=True)
        (ROOT / "source" / "build" / "signing-mode.txt").write_text(
            "development-debug-key\n", encoding="utf-8"
        )
        set_output("enabled", "false")
        return

    if not all(supplied):
        missing = [key for key, value in values.items() if not value]
        fail("missing one or more required Actions secrets: " + ", ".join(missing))

    if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", values["ANDROID_KEY_ALIAS"]):
        fail("ANDROID_KEY_ALIAS contains unsupported characters.")

    try:
        keystore_bytes = base64.b64decode(values["ANDROID_KEYSTORE_BASE64"], validate=True)
    except (binascii.Error, ValueError):
        fail("ANDROID_KEYSTORE_BASE64 is not valid single-line Base64.")

    if not 512 <= len(keystore_bytes) <= 512 * 1024:
        fail("decoded keystore has an unexpected size.")

    if not GRADLE_FILE.is_file():
        fail("expected Flutter Kotlin Gradle file was not generated.")

    gradle = GRADLE_FILE.read_text(encoding="utf-8")
    debug_line = 'signingConfig = signingConfigs.getByName("debug")'
    release_line = 'signingConfig = signingConfigs.getByName("release")'

    if debug_line not in gradle:
        fail("Flutter's expected release debug-signing line was not found.")
    if "create(\"release\")" in gradle:
        fail("release signing config already exists; refusing to duplicate it.")

    signing_config = """    signingConfigs {
        create("release") {
            keyAlias = System.getenv("ANDROID_KEY_ALIAS")
            keyPassword = System.getenv("ANDROID_KEY_PASSWORD")
            storeFile = file("release-keystore.jks")
            storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
        }
    }

"""
    gradle = gradle.replace("android {\n", "android {\n" + signing_config, 1)
    gradle = gradle.replace(debug_line, release_line, 1)

    if debug_line in gradle or release_line not in gradle:
        fail("could not switch the release build to the persistent signing config.")

    APP_DIR.mkdir(parents=True, exist_ok=True)
    KEYSTORE_FILE.write_bytes(keystore_bytes)
    KEYSTORE_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    GRADLE_FILE.write_text(gradle, encoding="utf-8")

    result = subprocess.run(
        [
            "keytool", "-list", "-keystore", str(KEYSTORE_FILE),
            "-storepass", values["ANDROID_KEYSTORE_PASSWORD"],
            "-alias", values["ANDROID_KEY_ALIAS"],
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        KEYSTORE_FILE.unlink(missing_ok=True)
        fail("keystore password or alias validation failed.")

    (ROOT / "source" / "build").mkdir(parents=True, exist_ok=True)
    (ROOT / "source" / "build" / "signing-mode.txt").write_text(
        "persistent-production-key\n", encoding="utf-8"
    )
    print("Persistent Android release signing configured and keystore alias validated.")
    set_output("enabled", "true")


if __name__ == "__main__":
    main()
