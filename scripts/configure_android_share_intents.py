#!/usr/bin/env python3
"""Configure Android ACTION_PROCESS_TEXT and ACTION_SEND integration."""

from pathlib import Path
import re
import textwrap

root = Path("source")
main_activities = list(
    (root / "android/app/src/main/kotlin").rglob("MainActivity.kt")
)
if len(main_activities) != 1:
    raise SystemExit(
        f"Expected exactly one generated MainActivity.kt, found {len(main_activities)}"
    )

main_activity = main_activities[0]
original = main_activity.read_text(encoding="utf-8")
package_match = re.search(r"(?m)^package\s+([A-Za-z0-9_.]+)\s*$", original)
if not package_match:
    raise SystemExit("Could not read the generated Android Kotlin package name")
package_name = package_match.group(1)

kotlin = r'''package __PACKAGE__

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

class MainActivity : FlutterActivity() {
    companion object {
        private const val SHARE_CHANNEL =
            "com.loudply.universaltranslator/shared_content"
        private const val MAX_SHARED_IMAGE_BYTES = 30L * 1024L * 1024L
    }

    private var shareChannel: MethodChannel? = null
    private var pendingSharedContent: Map<String, Any> = emptyMap()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pendingSharedContent = extractSharedContent(intent)
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        shareChannel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            SHARE_CHANNEL
        ).also { channel ->
            channel.setMethodCallHandler { call, result ->
                when (call.method) {
                    "getSharedContent" -> {
                        val payload = pendingSharedContent
                        pendingSharedContent = emptyMap()
                        result.success(payload)
                    }
                    else -> result.notImplemented()
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        val payload = extractSharedContent(intent)
        if (payload.isNotEmpty()) {
            pendingSharedContent = payload
            shareChannel?.invokeMethod("sharedContent", payload)
        }
    }

    private fun extractSharedContent(source: Intent?): Map<String, Any> {
        val incoming = source ?: return emptyMap()

        if (incoming.action == Intent.ACTION_PROCESS_TEXT) {
            val selected = incoming.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)
                ?.toString()
                ?.trim()
            if (!selected.isNullOrEmpty()) {
                return mapOf("text" to selected)
            }
        }

        if (incoming.action == Intent.ACTION_SEND) {
            val mimeType = incoming.type.orEmpty()
            if (mimeType.startsWith("text/")) {
                val text = incoming.getCharSequenceExtra(Intent.EXTRA_TEXT)
                    ?.toString()
                    ?.trim()
                if (!text.isNullOrEmpty()) {
                    return mapOf("text" to text)
                }
            }

            if (mimeType.startsWith("image/")) {
                val uri = sharedStreamUri(incoming)
                val path = uri?.let(::copySharedImageToCache)
                if (!path.isNullOrEmpty()) {
                    return mapOf("imagePath" to path)
                }
            }
        }

        if (incoming.action == Intent.ACTION_SEND_MULTIPLE &&
            incoming.type.orEmpty().startsWith("image/")) {
            val uri = incoming.clipData?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.uri
            val path = uri?.let(::copySharedImageToCache)
            if (!path.isNullOrEmpty()) {
                return mapOf("imagePath" to path)
            }
        }

        return emptyMap()
    }

    @Suppress("DEPRECATION")
    private fun sharedStreamUri(incoming: Intent): Uri? {
        return if (Build.VERSION.SDK_INT >= 33) {
            incoming.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
        } else {
            incoming.getParcelableExtra(Intent.EXTRA_STREAM) as? Uri
        } ?: incoming.clipData?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.uri
    }

    private fun copySharedImageToCache(uri: Uri): String? {
        return try {
            val mimeType = contentResolver.getType(uri).orEmpty()
            val extension = when (mimeType.lowercase()) {
                "image/jpeg", "image/jpg" -> "jpg"
                "image/png" -> "png"
                "image/webp" -> "webp"
                "image/heic" -> "heic"
                else -> "img"
            }
            val destination = File(
                cacheDir,
                "shared_translation_" + System.currentTimeMillis() + "." + extension
            )
            val input = contentResolver.openInputStream(uri) ?: return null
            input.use { stream ->
                FileOutputStream(destination).use { output ->
                    val buffer = ByteArray(16 * 1024)
                    var total = 0L
                    while (true) {
                        val count = stream.read(buffer)
                        if (count < 0) break
                        total += count
                        if (total > MAX_SHARED_IMAGE_BYTES) {
                            throw IOException("Shared image exceeds the 30 MB limit")
                        }
                        output.write(buffer, 0, count)
                    }
                    output.flush()
                }
            }
            destination.absolutePath
        } catch (error: Exception) {
            null
        }
    }
}
'''.replace("__PACKAGE__", package_name)

main_activity.write_text(kotlin, encoding="utf-8")

manifest = root / "android/app/src/main/AndroidManifest.xml"
xml = manifest.read_text(encoding="utf-8")
activity_pattern = re.compile(
    r'<activity\b(?=[^>]*android:name="[^"]*MainActivity")[\s\S]*?</activity>',
    re.MULTILINE,
)
match = activity_pattern.search(xml)
if not match:
    raise SystemExit("Generated Android manifest has no MainActivity block")
activity = match.group(0)

if 'android:launchMode="singleTop"' not in activity:
    activity = activity.replace(
        "<activity",
        '<activity android:launchMode="singleTop"',
        1,
    )

filters = [
    """            <intent-filter>
                <action android:name="android.intent.action.PROCESS_TEXT" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="text/plain" />
            </intent-filter>""",
    """            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="text/plain" />
            </intent-filter>""",
    """            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="image/*" />
            </intent-filter>""",
    """            <intent-filter>
                <action android:name="android.intent.action.SEND_MULTIPLE" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="image/*" />
            </intent-filter>""",
]

for intent_filter in filters:
    action_name = re.search(
        r'<action android:name="([^"]+)"',
        intent_filter,
    ).group(1)
    mime_type = re.search(
        r'<data android:mimeType="([^"]+)"',
        intent_filter,
    ).group(1)
    if action_name not in activity or mime_type not in activity:
        activity = activity.replace(
            "</activity>",
            textwrap.indent(intent_filter, "        ") + "\n        </activity>",
            1,
        )

xml = xml[:match.start()] + activity + xml[match.end():]
manifest.write_text(xml, encoding="utf-8")

print(f"Configured Android sharing intents for {package_name}")
print(f"Updated {main_activity}")
print(f"Updated {manifest}")
