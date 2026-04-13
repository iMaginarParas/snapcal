package com.steptracker.health_tracker

import android.Manifest
import android.content.*
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterFragmentActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.health.connect.client.HealthConnectClient

class MainActivity: FlutterFragmentActivity() {
    private val METHOD_CHANNEL = "health_bridge"
    private val EVENT_CHANNEL = "step_event_channel"
    
    private var healthConnectManager: HealthConnectManager? = null
    private val scope = CoroutineScope(Dispatchers.Main)
    private var pendingResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        // Setup Health Connect Manager
        try {
            if (HealthConnectClient.getSdkStatus(this) == HealthConnectClient.SDK_AVAILABLE) {
                healthConnectManager = HealthConnectManager(this)
            }
        } catch (e: Exception) {
             android.util.Log.e("MainActivity", "HealthSDK not available")
        }

        // Setup EventChannel (Live Push Stream)
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, EVENT_CHANNEL).setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    StepForegroundService.stepUpdateListener = { steps ->
                        runOnUiThread { events?.success(steps) }
                    }
                }
                override fun onCancel(arguments: Any?) {
                    StepForegroundService.stepUpdateListener = null
                }
            }
        )

        // MethodChannel Handling (for one-off requests)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, METHOD_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "requestPermissions" -> {
                    pendingResult = result
                    if (!hasRequiredPermissions()) {
                        requestRequiredPermissions()
                    } else {
                        // Activity Recognition granted, check Health Connect
                        startTrackingService()
                        checkHealthConnectPermissions()
                    }
                }
                "getTodaySteps" -> {
                    // Pulling from persistent storage for maximum accuracy
                    val prefs = getSharedPreferences("StepTrackerPrefs", Context.MODE_PRIVATE)
                    val liveSteps = prefs.getLong("liveSessionSteps", 0L)
                    scope.launch {
                        try {
                            val cloudSteps = healthConnectManager?.getTodaySteps() ?: 0L
                            result.success(cloudSteps + liveSteps)
                        } catch (e: Exception) {
                            result.success(liveSteps)
                        }
                    }
                }
                "getTodayDistance", "getWeeklySteps" -> {
                    val manager = healthConnectManager
                    if (manager == null) {
                        result.success(if (call.method == "getWeeklySteps") "[]" else 0.0)
                        return@setMethodCallHandler
                    }
                    scope.launch {
                        try {
                            if (call.method == "getTodayDistance") result.success(manager.getTodayDistance())
                            else result.success(manager.getWeeklySteps())
                        } catch (e: Exception) {
                            result.success(if (call.method == "getWeeklySteps") "[]" else 0.0)
                        }
                    }
                }
                "isStepTrackingSupported" -> {
                    val pm = packageManager
                    val hasSensor = pm.hasSystemFeature(PackageManager.FEATURE_SENSOR_STEP_COUNTER) 
                                 || pm.hasSystemFeature(PackageManager.FEATURE_SENSOR_STEP_DETECTOR)
                    val hasHealthConnect = healthConnectManager != null
                    result.success(hasSensor || hasHealthConnect)
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun checkHealthConnectPermissions() {
        scope.launch {
            val manager = healthConnectManager
            if (manager == null) {
                pendingResult?.success(true)
                pendingResult = null
                return@launch
            }
            
            if (manager.hasAllPermissions()) {
                pendingResult?.success(true)
                pendingResult = null
            } else {
                manager.requestPermissionsLauncher(this@MainActivity)
            }
        }
    }

    private fun hasRequiredPermissions(): Boolean {
        val permissions = mutableListOf(Manifest.permission.ACTIVITY_RECOGNITION)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        return permissions.all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }
    }

    private fun requestRequiredPermissions() {
        val permissions = mutableListOf(Manifest.permission.ACTIVITY_RECOGNITION)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        ActivityCompat.requestPermissions(this, permissions.toTypedArray(), 5002)
    }

    private fun startTrackingService() {
        if (!StepForegroundService.isServiceRunning) {
            val serviceIntent = Intent(this, StepForegroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 5002) {
            if (grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                startTrackingService()
                // Now check Health Connect sequence
                checkHealthConnectPermissions()
            } else {
                pendingResult?.success(false)
                pendingResult = null
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 5001) {
            scope.launch {
                val granted = healthConnectManager?.hasAllPermissions() ?: false
                pendingResult?.success(granted)
                pendingResult = null
            }
        }
    }
}
