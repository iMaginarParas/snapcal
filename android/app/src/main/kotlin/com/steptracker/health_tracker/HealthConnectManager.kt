package com.steptracker.health_tracker

import android.app.Activity
import android.content.Context
import android.content.Intent
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.DistanceRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import java.time.Instant
import java.time.ZonedDateTime
import java.time.temporal.ChronoUnit
import org.json.JSONArray
import org.json.JSONObject

class HealthConnectManager(private val context: Context) {
    private val healthConnectClient by lazy { HealthConnectClient.getOrCreate(context) }

    val permissions = setOf(
        HealthPermission.getReadPermission(StepsRecord::class),
        HealthPermission.getReadPermission(DistanceRecord::class)
    )

    suspend fun hasAllPermissions(): Boolean {
        return try {
            val granted = healthConnectClient.permissionController.getGrantedPermissions()
            granted.containsAll(permissions)
        } catch (e: Exception) {
            false
        }
    }

    fun requestPermissionsLauncher(activity: Activity) {
        try {
            val intent = Intent("androidx.health.connect.action.REQUEST_PERMISSIONS")
            intent.putExtra("androidx.health.connect.extra.PERMISSION_LIST", ArrayList(permissions))
            activity.startActivityForResult(intent, 5001)
        } catch (e: Exception) {
             android.util.Log.e("HealthConnectManager", "Failed to launch intent", e)
        }
    }

    suspend fun getTodaySteps(): Long {
        return try {
            val startOfDay = ZonedDateTime.now().toLocalDate().atStartOfDay(ZonedDateTime.now().zone).toInstant()
            val endOfDay = Instant.now()
            
            val response = healthConnectClient.readRecords(
                ReadRecordsRequest(
                    StepsRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(startOfDay, endOfDay)
                )
            )
            response.records.sumOf { it.count }
        } catch (e: Exception) {
            0L
        }
    }

    suspend fun getTodayDistance(): Double {
        return try {
            val startOfDay = ZonedDateTime.now().toLocalDate().atStartOfDay(ZonedDateTime.now().zone).toInstant()
            val endOfDay = Instant.now()
            
            val response = healthConnectClient.readRecords(
                ReadRecordsRequest(
                    DistanceRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(startOfDay, endOfDay)
                )
            )
            response.records.sumOf { it.distance.inMeters }
        } catch (e: Exception) {
             0.0
        }
    }

    suspend fun getWeeklySteps(): String {
        return try {
            val endTime = Instant.now()
            val startTime = endTime.minus(7, ChronoUnit.DAYS)
            
            val response = healthConnectClient.readRecords(
                ReadRecordsRequest(
                    StepsRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(startTime, endTime)
                )
            )

            val weeklyData = JSONArray()
            response.records.forEach { record ->
                val obj = JSONObject()
                obj.put("steps", record.count)
                obj.put("timestamp", record.startTime.toString())
                weeklyData.put(obj)
            }
            weeklyData.toString()
        } catch (e: Exception) {
            "[]"
        }
    }
}
