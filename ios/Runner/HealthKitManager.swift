import Foundation
import HealthKit

class HealthKitManager {
    let healthStore = HKHealthStore()
    
    func requestPermissions(completion: @escaping (Bool, Error?) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            completion(false, nil)
            return
        }
        
        let typesToRead: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .stepCount)!,
            HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning)!
        ]
        
        healthStore.requestAuthorization(toShare: nil, read: typesToRead) { (success, error) in
            completion(success, error)
        }
    }
    
    func getTodaySteps(completion: @escaping (Double) -> Void) {
        let stepsQuantityType = HKQuantityType.quantityType(forIdentifier: .stepCount)!
        
        let now = Date()
        let startOfDay = Calendar.current.startOfDay(for: now)
        let predicate = HKQuery.predicateForSamples(withStart: startOfDay, end: now, options: .strictStartDate)
        
        let query = HKStatisticsQuery(quantityType: stepsQuantityType, quantitySamplePredicate: predicate, options: .cumulativeSum) { (_, result, _) in
            guard let result = result, let sum = result.sumQuantity() else {
                completion(0.0)
                return
            }
            completion(sum.doubleValue(for: HKUnit.count()))
        }
        
        healthStore.execute(query)
    }
    
    func getTodayDistance(completion: @escaping (Double) -> Void) {
        let distanceQuantityType = HKQuantityType.quantityType(forIdentifier: .distanceWalkingRunning)!
        
        let now = Date()
        let startOfDay = Calendar.current.startOfDay(for: now)
        let predicate = HKQuery.predicateForSamples(withStart: startOfDay, end: now, options: .strictStartDate)
        
        let query = HKStatisticsQuery(quantityType: distanceQuantityType, quantitySamplePredicate: predicate, options: .cumulativeSum) { (_, result, _) in
            guard let result = result, let sum = result.sumQuantity() else {
                completion(0.0)
                return
            }
            completion(sum.doubleValue(for: HKUnit.meter()))
        }
        
        healthStore.execute(query)
    }
    
    func getWeeklySteps(completion: @escaping (String) -> Void) {
        let stepsQuantityType = HKQuantityType.quantityType(forIdentifier: .stepCount)!
        let now = Date()
        let calendar = Calendar.current
        let startOfWeek = calendar.date(byAdding: .day, value: -7, to: now)!
        
        let predicate = HKQuery.predicateForSamples(withStart: startOfWeek, end: now, options: .strictStartDate)
        
        var interval = DateComponents()
        interval.day = 1
        
        let query = HKStatisticsCollectionQuery(quantityType: stepsQuantityType, quantitySamplePredicate: predicate, options: .cumulativeSum, anchorDate: startOfWeek, intervalComponents: interval)
        
        query.initialResultsHandler = { _, results, error in
            var weeklyData: [[String: Any]] = []
            
            results?.enumerateStatistics(from: startOfWeek, to: now) { statistics, _ in
                let steps = statistics.sumQuantity()?.doubleValue(for: HKUnit.count()) ?? 0
                let dateString = ISO8601DateFormatter().string(from: statistics.startDate)
                
                weeklyData.append([
                    "steps": Int(steps),
                    "distance": 0.0,
                    "timestamp": dateString
                ])
            }
            
            if let jsonData = try? JSONSerialization.data(withJSONObject: weeklyData, options: []),
               let jsonString = String(data: jsonData, encoding: .utf8) {
                completion(jsonString)
            } else {
                completion("[]")
            }
        }
        
        healthStore.execute(query)
    }
}
