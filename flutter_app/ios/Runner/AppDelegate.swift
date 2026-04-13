import Flutter
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate {
  let healthKitManager = HealthKitManager()

  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    let controller : FlutterViewController = window?.rootViewController as! FlutterViewController
    let healthChannel = FlutterMethodChannel(name: "health_bridge",
                                              binaryMessenger: controller.binaryMessenger)
    
    healthChannel.setMethodCallHandler({
      (call: FlutterMethodCall, result: @escaping FlutterResult) -> Void in
      
      switch call.method {
      case "isStepTrackingSupported":
        result(HKHealthStore.isHealthDataAvailable())
      case "requestPermissions":
        self.healthKitManager.requestPermissions { success, error in
          result(success)
        }
      case "getTodaySteps":
        self.healthKitManager.getTodaySteps { steps in
          result(Int(steps))
        }
      case "getTodayDistance":
        self.healthKitManager.getTodayDistance { distance in
          result(distance)
        }
      case "getWeeklySteps":
        self.healthKitManager.getWeeklySteps { jsonString in
          result(jsonString)
        }
      case "startTracking", "stopTracking":
        result(true) // Native implementation can start background tracking if needed
      default:
        result(FlutterMethodNotImplemented)
      }
    })

    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
}
