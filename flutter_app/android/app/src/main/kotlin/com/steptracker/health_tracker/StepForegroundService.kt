package com.steptracker.health_tracker

import android.app.*
import android.content.*
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.*
import android.util.Log
import androidx.core.app.NotificationCompat
import java.util.Calendar

class StepForegroundService : Service(), SensorEventListener {
    private val TAG = "StepForegroundService"
    private val NOTIFICATION_ID = 888
    private val CHANNEL_ID = "step_tracker_channel"

    private var sensorManager: SensorManager? = null
    private var stepCounterSensor: Sensor? = null
    private var stepDetectorSensor: Sensor? = null

    // Persistent State
    private var liveSessionSteps = 0L
    private var initialStepCount = -1L
    private var lastUpdateDay = -1

    companion object {
        var isServiceRunning = false
        var stepUpdateListener: ((Long) -> Unit)? = null
    }

    override fun onCreate() {
        super.onCreate()
        isServiceRunning = true
        loadSteps()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())

        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        stepCounterSensor = sensorManager?.getDefaultSensor(Sensor.TYPE_STEP_COUNTER)
        stepDetectorSensor = sensorManager?.getDefaultSensor(Sensor.TYPE_STEP_DETECTOR)

        registerSensors()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        registerSensors()
        return START_STICKY
    }

    private fun registerSensors() {
        stepDetectorSensor?.let { sensorManager?.registerListener(this, it, SensorManager.SENSOR_DELAY_UI) }
        stepCounterSensor?.let { sensorManager?.registerListener(this, it, SensorManager.SENSOR_DELAY_UI) }
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null) return
        checkMidnightReset()

        when (event.sensor.type) {
            Sensor.TYPE_STEP_DETECTOR -> {
                liveSessionSteps += 1
                notifyUpdate()
            }
            Sensor.TYPE_STEP_COUNTER -> {
                val totalStepsSinceReboot = event.values[0].toLong()
                if (initialStepCount == -1L) {
                    initialStepCount = totalStepsSinceReboot
                    saveSteps()
                } else {
                    val actualLive = (totalStepsSinceReboot - initialStepCount).coerceAtLeast(0L)
                    if (actualLive > liveSessionSteps) {
                        liveSessionSteps = actualLive
                        notifyUpdate()
                    }
                }
            }
        }
    }

    private fun notifyUpdate() {
        saveSteps()
        stepUpdateListener?.invoke(liveSessionSteps)
        updateNotification()
    }

    private fun checkMidnightReset() {
        val today = Calendar.getInstance().get(Calendar.DAY_OF_YEAR)
        if (lastUpdateDay != -1 && lastUpdateDay != today) {
            liveSessionSteps = 0L
            initialStepCount = -1L
            saveSteps()
            Log.i(TAG, "Midnight Reset Successfully Performed")
        }
        lastUpdateDay = today
    }

    private fun loadSteps() {
        val prefs = getSharedPreferences("StepTrackerPrefs", Context.MODE_PRIVATE)
        liveSessionSteps = prefs.getLong("liveSessionSteps", 0L)
        initialStepCount = prefs.getLong("initialStepCount", -1L)
        lastUpdateDay = prefs.getInt("lastUpdateDay", -1)
    }

    private fun saveSteps() {
        val prefs = getSharedPreferences("StepTrackerPrefs", Context.MODE_PRIVATE)
        prefs.edit().apply {
            putLong("liveSessionSteps", liveSessionSteps)
            putLong("initialStepCount", initialStepCount)
            putInt("lastUpdateDay", lastUpdateDay)
            apply()
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID, "Step Tracking Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(serviceChannel)
        }
    }

    private fun buildNotification(): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("StepTracker is active")
            .setContentText("Current steps: $liveSessionSteps")
            .setSmallIcon(android.R.drawable.ic_menu_directions)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    private fun updateNotification() {
        val manager = getSystemService(NotificationManager::class.java)
        manager?.notify(NOTIFICATION_ID, buildNotification())
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        isServiceRunning = false
        sensorManager?.unregisterListener(this)
    }
}
