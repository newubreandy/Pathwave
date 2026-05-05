import Flutter
import UIKit
import NetworkExtension

/// PathWave iOS — WiFi 자동 가입 native plugin (PR #49).
///
/// `NEHotspotConfigurationManager` 로 OS 에 WiFi 가입을 요청. 앱 capabilities 에
/// `Hotspot Configuration` 활성화 + Runner.entitlements 에
/// `com.apple.developer.networking.HotspotConfiguration = YES` 필수.
@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  private let channelName = "pathwave/wifi"

  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    if let controller = window?.rootViewController as? FlutterViewController {
      registerWifiChannel(on: controller)
    }
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    if let controller = window?.rootViewController as? FlutterViewController {
      registerWifiChannel(on: controller)
    }
  }

  private func registerWifiChannel(on controller: FlutterViewController) {
    let channel = FlutterMethodChannel(
      name: channelName,
      binaryMessenger: controller.binaryMessenger
    )
    channel.setMethodCallHandler { [weak self] call, result in
      guard let self = self else { return }
      switch call.method {
      case "connect":
        self.handleConnect(call: call, result: result)
      case "remove":
        self.handleRemove(call: call, result: result)
      default:
        result(FlutterMethodNotImplemented)
      }
    }
  }

  private func handleConnect(call: FlutterMethodCall, result: @escaping FlutterResult) {
    let args = call.arguments as? [String: Any] ?? [:]
    let ssid = args["ssid"] as? String ?? ""
    let password = args["password"] as? String ?? ""
    if ssid.isEmpty {
      result(FlutterError(code: "invalid_args", message: "ssid is required", details: nil))
      return
    }
    let config: NEHotspotConfiguration
    if password.isEmpty {
      config = NEHotspotConfiguration(ssid: ssid)   // 개방형
    } else {
      config = NEHotspotConfiguration(ssid: ssid, passphrase: password, isWEP: false)
    }
    config.joinOnce = false   // 즉시 사라지지 않게 등록
    NEHotspotConfigurationManager.shared.apply(config) { error in
      if let nsErr = error as NSError? {
        // alreadyAssociated / userDenied 는 성공/취소 분기.
        if nsErr.domain == NEHotspotConfigurationErrorDomain {
          let code = NEHotspotConfigurationError(rawValue: nsErr.code)
          if code == .alreadyAssociated {
            result(["ok": true, "method": "alreadyAssociated"])
            return
          }
          if code == .userDenied {
            result(FlutterError(code: "user_denied",
                                message: "사용자가 WiFi 가입을 거부했습니다.",
                                details: nil))
            return
          }
        }
        result(FlutterError(code: "connect_failed",
                            message: nsErr.localizedDescription,
                            details: nil))
        return
      }
      result(["ok": true, "method": "applied"])
    }
  }

  private func handleRemove(call: FlutterMethodCall, result: @escaping FlutterResult) {
    let args = call.arguments as? [String: Any] ?? [:]
    let ssid = args["ssid"] as? String ?? ""
    if ssid.isEmpty {
      result(FlutterError(code: "invalid_args", message: "ssid is required", details: nil))
      return
    }
    NEHotspotConfigurationManager.shared.removeConfiguration(forSSID: ssid)
    result(true)
  }
}
