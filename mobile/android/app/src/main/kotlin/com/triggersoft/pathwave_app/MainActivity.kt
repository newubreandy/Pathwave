package com.triggersoft.pathwave_app

import android.content.Context
import android.net.wifi.WifiManager
import android.net.wifi.WifiNetworkSuggestion
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * PathWave Android — WiFi 자동 가입 native plugin (PR #49).
 *
 * 백엔드 BLE 핸드셰이크에서 받은 SSID/password 로 OS 가 WiFi 에 가입하도록
 * 시스템에 제안. Android 10 (API 29) 이상은 WifiNetworkSuggestion 권장.
 * 이하 버전은 OS 제한으로 자동 가입 미지원.
 */
class MainActivity : FlutterActivity() {
    private val channelName = "pathwave/wifi"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "connect" -> handleConnect(call, result)
                    "remove"  -> handleRemove(call, result)
                    else      -> result.notImplemented()
                }
            }
    }

    private fun handleConnect(
        call: io.flutter.plugin.common.MethodCall,
        result: MethodChannel.Result,
    ) {
        val ssid = call.argument<String>("ssid") ?: ""
        val password = call.argument<String>("password") ?: ""
        if (ssid.isEmpty()) {
            result.error("invalid_args", "ssid is required", null); return
        }
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                connectQ(ssid, password)
                result.success(mapOf("ok" to true, "method" to "suggestion"))
            } else {
                result.error(
                    "unsupported_os",
                    "Android 10 미만은 OS 제한으로 자동 가입을 지원하지 않습니다.",
                    null,
                )
            }
        } catch (e: Throwable) {
            result.error("connect_failed", e.message, null)
        }
    }

    private fun handleRemove(
        call: io.flutter.plugin.common.MethodCall,
        result: MethodChannel.Result,
    ) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val wifi = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
                wifi.removeNetworkSuggestions(emptyList())
                result.success(true)
            } else {
                result.success(false)
            }
        } catch (e: Throwable) {
            result.error("remove_failed", e.message, null)
        }
    }

    /** Android 10+ — WifiNetworkSuggestion. 사용자 알림이 1회 표시됨. */
    private fun connectQ(ssid: String, password: String) {
        val wifi = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
        val builder = WifiNetworkSuggestion.Builder().setSsid(ssid)
        if (password.isNotEmpty()) builder.setWpa2Passphrase(password)
        // 동일 SSID 의 기존 등록 정리 (PathWave 전용 가정)
        try { wifi.removeNetworkSuggestions(emptyList()) } catch (_: Throwable) {}
        val suggestion = builder.build()
        val status = wifi.addNetworkSuggestions(listOf(suggestion))
        if (status != WifiManager.STATUS_NETWORK_SUGGESTIONS_SUCCESS &&
            status != WifiManager.STATUS_NETWORK_SUGGESTIONS_ERROR_ADD_DUPLICATE
        ) {
            throw RuntimeException("addNetworkSuggestions status=$status")
        }
    }
}
