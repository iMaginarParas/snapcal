import fs from 'fs';
import path from 'path';

const storageDir = path.join(__dirname, '../../data');
const storageFile = path.join(storageDir, 'storage.json');

interface FallbackDb {
  users: { [id: string]: any };
  meals: { [id: string]: any[] };
  workouts: { [id: string]: any[] };
  dailyStats: { [id: string]: { [date: string]: any } };
}

let db: FallbackDb = {
  users: {},
  meals: {},
  workouts: {},
  dailyStats: {}
};

export function initFallbackDb() {
  if (!fs.existsSync(storageDir)) {
    fs.mkdirSync(storageDir, { recursive: true });
  }
  if (fs.existsSync(storageFile)) {
    try {
      const data = fs.readFileSync(storageFile, 'utf8');
      db = JSON.parse(data);
      if (!db.users) db.users = {};
      if (!db.meals) db.meals = {};
      if (!db.workouts) db.workouts = {};
      if (!db.dailyStats) db.dailyStats = {};
    } catch (e) {
      console.error('Failed to parse fallback storage.json. Initializing empty.');
    }
  } else {
    saveDb();
  }
}

function saveDb() {
  try {
    fs.writeFileSync(storageFile, JSON.stringify(db, null, 2), 'utf8');
  } catch (e) {
    console.error('Failed to write to fallback storage.json:', e);
  }
}

// Local Database Fallback API
export const fallbackDb = {
  getUser: (id: string) => {
    if (!db.users[id]) {
      db.users[id] = { id, email: `${id}@fallback.local`, name: 'Guest User', age: 25, weight: 76.4, height: 178, goals: 'Build Muscle', profile_picture_url: null };
      saveDb();
    }
    return db.users[id];
  },
  updateUser: (id: string, updates: any) => {
    const user = fallbackDb.getUser(id);
    db.users[id] = { ...user, ...updates };
    saveDb();
    return db.users[id];
  },
  getMeals: (userId: string) => {
    return db.meals[userId] || [];
  },
  addMeal: (userId: string, meal: any) => {
    if (!db.meals[userId]) db.meals[userId] = [];
    const newMeal = {
      id: Math.random().toString(36).substring(2, 11),
      user_id: userId,
      name: meal.name,
      calories: meal.calories,
      protein: meal.protein || 0,
      carbs: meal.carbs || 0,
      fats: meal.fats || 0,
      image_url: meal.image_url || null,
      logged_at: new Date().toISOString()
    };
    db.meals[userId].push(newMeal);
    saveDb();
    return newMeal;
  },
  getWorkouts: (userId: string) => {
    return db.workouts[userId] || [];
  },
  addWorkout: (userId: string, workout: any) => {
    if (!db.workouts[userId]) db.workouts[userId] = [];
    const newWorkout = {
      id: Math.random().toString(36).substring(2, 11),
      user_id: userId,
      workout_name: workout.workout_name,
      distance: workout.distance || 0,
      duration_seconds: workout.duration_seconds || 0,
      calories: workout.calories || 0,
      route_points: workout.route_points || [],
      completed: true,
      completed_at: new Date().toISOString()
    };
    db.workouts[userId].push(newWorkout);
    saveDb();
    return newWorkout;
  },
  getDailyStats: (userId: string, dateStr: string) => {
    if (!db.dailyStats[userId]) db.dailyStats[userId] = {};
    if (!db.dailyStats[userId][dateStr]) {
      db.dailyStats[userId][dateStr] = {
        id: Math.random().toString(36).substring(2, 11),
        user_id: userId,
        date: dateStr,
        steps: 0,
        water_ml: 0
      };
      saveDb();
    }
    return db.dailyStats[userId][dateStr];
  },
  updateDailyStats: (userId: string, dateStr: string, updates: { steps?: number; water_ml?: number }) => {
    const stats = fallbackDb.getDailyStats(userId, dateStr);
    if (updates.steps !== undefined) stats.steps = updates.steps;
    if (updates.water_ml !== undefined) stats.water_ml = updates.water_ml;
    db.dailyStats[userId][dateStr] = stats;
    saveDb();
    return stats;
  }
};
