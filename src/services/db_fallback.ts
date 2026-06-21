import fs from 'fs';
import path from 'path';

const storageDir = path.join(__dirname, '../../data');
const storageFile = path.join(storageDir, 'storage.json');

interface FallbackDb {
  users: { [id: string]: any };
  meals: { [id: string]: any[] };
  workouts: { [id: string]: any[] };
  dailyStats: { [id: string]: { [date: string]: any } };
  measurementLogs: { [id: string]: any[] };
  fastingLogs: { [id: string]: any[] };
  groups: any[];
  groupMembers: { [groupId: string]: string[] };
  groupMessages: { [groupId: string]: any[] };
  friendships: { [userId: string]: any[] };
  challenges: any[];
  userChallenges: { [userId: string]: any[] };
}

let db: FallbackDb = {
  users: {},
  meals: {},
  workouts: {},
  dailyStats: {},
  measurementLogs: {},
  fastingLogs: {},
  groups: [],
  groupMembers: {},
  groupMessages: {},
  friendships: {},
  challenges: [],
  userChallenges: {}
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
      if (!db.measurementLogs) db.measurementLogs = {};
      if (!db.fastingLogs) db.fastingLogs = {};
      if (!db.groups) db.groups = [];
      if (!db.groupMembers) db.groupMembers = {};
      if (!db.groupMessages) db.groupMessages = {};
      if (!db.friendships) db.friendships = {};
      if (!db.challenges) db.challenges = [];
      if (!db.userChallenges) db.userChallenges = {};

      if (db.challenges.length === 0) {
        db.challenges = [{
          id: 'default_challenge_core_crusher',
          title: '7-Day Core Crusher',
          description: 'Complete 5 core workouts this week to earn the exclusive Golden Abs badge.',
          target_workouts: 5,
          points: 500,
          created_at: new Date().toISOString()
        }];
        saveDb();
      }
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
      workout_type: workout.workout_type || 'cardio',
      category: workout.category || null,
      exercises: workout.exercises || null,
      completed: true,
      completed_at: new Date().toISOString()
    };
    db.workouts[userId].push(newWorkout);
    saveDb();
    return newWorkout;
  },
  deleteWorkout: (userId: string, id: string) => {
    if (!db.workouts[userId]) return false;
    const initialLength = db.workouts[userId].length;
    db.workouts[userId] = db.workouts[userId].filter(w => w.id !== id);
    if (db.workouts[userId].length < initialLength) {
      saveDb();
      return true;
    }
    return false;
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
  },
  getMeasurements: (userId: string, metricType?: string) => {
    const logs = db.measurementLogs[userId] || [];
    if (metricType) {
      return logs.filter(l => l.metric_type === metricType);
    }
    return logs.sort((a, b) => new Date(b.logged_at).getTime() - new Date(a.logged_at).getTime());
  },
  addMeasurement: (userId: string, metric: any) => {
    if (!db.measurementLogs[userId]) db.measurementLogs[userId] = [];
    const now = new Date();
    const ListMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const formattedDate = metric.date || `${ListMonths[now.getMonth()]} ${now.getDate().toString().padStart(2, '0')}, ${now.getFullYear()}`;
    const newMetric = {
      id: Math.random().toString(36).substring(2, 11),
      user_id: userId,
      metric_type: metric.metric_type,
      value: metric.value,
      logged_at: now.toISOString(),
      date: formattedDate
    };
    db.measurementLogs[userId].push(newMetric);
    saveDb();
    return newMetric;
  },
  deleteMeasurement: (userId: string, id: string) => {
    if (!db.measurementLogs[userId]) return false;
    const initialLength = db.measurementLogs[userId].length;
    db.measurementLogs[userId] = db.measurementLogs[userId].filter(l => l.id !== id);
    if (db.measurementLogs[userId].length < initialLength) {
      saveDb();
      return true;
    }
    return false;
  },

  // Fasting Methods
  getActiveFast: (userId: string) => {
    const list = db.fastingLogs[userId] || [];
    return list.find(f => !f.completed);
  },
  startFast: (userId: string, protocol: string) => {
    if (!db.fastingLogs[userId]) db.fastingLogs[userId] = [];
    const active = db.fastingLogs[userId].find(f => !f.completed);
    if (active) return active;
    const newFast = {
      id: Math.random().toString(36).substring(2, 11),
      user_id: userId,
      protocol,
      start_time: new Date().toISOString(),
      completed: false
    };
    db.fastingLogs[userId].push(newFast);
    saveDb();
    return newFast;
  },
  stopFast: (userId: string, id: string) => {
    if (!db.fastingLogs[userId]) return null;
    const fast = db.fastingLogs[userId].find(f => f.id === id);
    if (fast) {
      fast.completed = true;
      fast.end_time = new Date().toISOString();
      saveDb();
    }
    return fast;
  },
  getFastingHistory: (userId: string) => {
    const list = db.fastingLogs[userId] || [];
    return list.filter(f => f.completed).sort((a, b) => new Date(b.end_time).getTime() - new Date(a.end_time).getTime());
  },

  // Groups Methods
  getGroups: (userId: string) => {
    if (db.groups.length === 0) {
      db.groups = [
        { id: 'g_fitness_workouts', name: 'Fitness & Workouts', description: 'Share daily workouts that match your calorie goals, keep each other accountable.', is_public: true, created_by: 'system', created_at: new Date().toISOString() },
        { id: 'g_new_calorie', name: 'New to Calorie Tracking', description: 'Beginner questions, quick meal tips, tracking shortcuts, and celebrating first wins.', is_public: true, created_by: 'system', created_at: new Date().toISOString() },
        { id: 'g_muscle_gain', name: 'Muscle Gain & Bulking', description: 'Strategies for eating in a clean surplus, protein recipes, and heavy weight lifting.', is_public: true, created_by: 'system', created_at: new Date().toISOString() },
        { id: 'g_clean_fasting', name: 'Clean Fasting Habits', description: 'Share your intermittent fasting protocols, water fasting tips, and support.', is_public: true, created_by: 'system', created_at: new Date().toISOString() }
      ];
      db.groupMembers['g_fitness_workouts'] = ['system', 'JD', 'RS', 'A'];
      db.groupMembers['g_new_calorie'] = ['system', 'M', 'TL', 'BK'];
      db.groupMembers['g_muscle_gain'] = ['system', 'P', 'SO', 'D'];
      db.groupMembers['g_clean_fasting'] = ['system', 'E', 'W', 'CH'];
      saveDb();
    }
    return db.groups.filter(g => {
      const members = db.groupMembers[g.id] || [];
      return g.is_public || g.created_by === userId || members.includes(userId);
    }).map(g => {
      const members = db.groupMembers[g.id] || [];
      return {
        ...g,
        memberCount: members.length,
        isJoined: members.includes(userId),
        avatars: members.slice(0, 3).map(mid => {
          if (mid === 'system') return 'SYS';
          const u = db.users[mid];
          return u ? (u.name || 'US').split(' ').map((e: any) => e[0]).slice(0, 2).join('').toUpperCase() : 'US';
        }),
        extraMemberText: members.length > 3 ? `+${members.length - 3}` : '',
        tag: g.created_by === 'system' ? 'Trending' : 'New'
      };
    });
  },
  createGroup: (userId: string, group: any) => {
    const newGroup = {
      id: Math.random().toString(36).substring(2, 11),
      name: group.name,
      description: group.description,
      is_public: group.is_public !== false,
      created_by: userId,
      created_at: new Date().toISOString()
    };
    db.groups.push(newGroup);
    db.groupMembers[newGroup.id] = [userId];
    saveDb();
    return {
      ...newGroup,
      memberCount: 1,
      isJoined: true,
      avatars: ['ME'],
      extraMemberText: '',
      tag: 'New'
    };
  },
  joinGroup: (userId: string, groupId: string) => {
    if (!db.groupMembers[groupId]) db.groupMembers[groupId] = [];
    if (!db.groupMembers[groupId].includes(userId)) {
      db.groupMembers[groupId].push(userId);
      saveDb();
    }
    const group = db.groups.find(g => g.id === groupId);
    return group ? { ...group, memberCount: db.groupMembers[groupId].length, isJoined: true } : null;
  },
  leaveGroup: (userId: string, groupId: string) => {
    if (db.groupMembers[groupId]) {
      db.groupMembers[groupId] = db.groupMembers[groupId].filter(id => id !== userId);
      saveDb();
    }
    const group = db.groups.find(g => g.id === groupId);
    return group ? { ...group, memberCount: db.groupMembers[groupId].length, isJoined: false } : null;
  },

  // Group Messages Methods
  getGroupMessages: (groupId: string) => {
    return db.groupMessages[groupId] || [];
  },
  sendGroupMessage: (userId: string, groupId: string, message: string) => {
    if (!db.groupMessages[groupId]) db.groupMessages[groupId] = [];
    const user = fallbackDb.getUser(userId);
    const newMessage = {
      id: Math.random().toString(36).substring(2, 11),
      group_id: groupId,
      user_id: userId,
      message,
      created_at: new Date().toISOString(),
      sender_name: user.name || 'Guest User'
    };
    db.groupMessages[groupId].push(newMessage);
    saveDb();
    return newMessage;
  },

  // Friends Methods
  getFriends: (userId: string) => {
    if (!db.friendships[userId] || db.friendships[userId].length === 0) {
      db.friendships[userId] = [];
      const defaultFriends = [
        { id: 'f_sarah', name: 'Sarah Miller', email: 'sarah.m@fitflow.ai' },
        { id: 'f_alex', name: 'Alex Johnson', email: 'alex.j@fitflow.ai' },
        { id: 'f_john', name: 'John Doe', email: 'john.d@fitflow.ai' },
        { id: 'f_emma', name: 'Emma Wilson', email: 'emma.w@fitflow.ai' }
      ];
      defaultFriends.forEach(df => {
        db.users[df.id] = { id: df.id, email: df.email, name: df.name, age: 25, weight: 70, height: 170, goals: 'Stay Healthy', profile_picture_url: null };
        
        const todayStr = new Date().toISOString().split('T')[0];
        if (!db.dailyStats[df.id]) db.dailyStats[df.id] = {};
        db.dailyStats[df.id][todayStr] = { steps: 5000 + Math.floor(Math.random() * 6000) };

        db.friendships[userId].push({
          id: Math.random().toString(36).substring(2, 11),
          user_id: userId,
          friend_id: df.id,
          status: 'accepted',
          created_at: new Date().toISOString()
        });
      });
      saveDb();
    }

    const list = db.friendships[userId] || [];
    return list.map(f => {
      const friendUser = fallbackDb.getUser(f.friend_id);
      const todayStr = new Date().toISOString().split('T')[0];
      const stats = fallbackDb.getDailyStats(f.friend_id, todayStr);
      return {
        id: f.id,
        friend_id: f.friend_id,
        name: friendUser.name || 'Friend User',
        email: friendUser.email,
        steps: stats.steps || 0,
        calories: Math.round((stats.steps || 0) * 0.045),
        avatar: (friendUser.name || 'FR').split(' ').map((e: any) => e[0]).slice(0, 2).join('').toUpperCase(),
        status: 'Active'
      };
    });
  },
  addFriendByEmail: (userId: string, email: string) => {
    const searchVal = email.trim();
    const friendId = Object.keys(db.users).find(uid => 
      db.users[uid].email.toLowerCase() === searchVal.toLowerCase() ||
      db.users[uid].name.toLowerCase() === searchVal.toLowerCase()
    );
    if (!friendId) {
      const mockId = searchVal.replace(/[^a-zA-Z0-9]/g, '_');
      const isEmail = searchVal.includes('@');
      const mockEmail = isEmail ? searchVal : `${searchVal.toLowerCase()}@sabtrack.com`;
      const mockName = isEmail ? searchVal.split('@')[0].toUpperCase() : searchVal.toUpperCase();

      db.users[mockId] = { id: mockId, email: mockEmail, name: mockName, age: 25, weight: 70, height: 170, goals: 'Stay Healthy', profile_picture_url: null };
      saveDb();
      return fallbackDb.createFriendship(userId, mockId);
    }
    return fallbackDb.createFriendship(userId, friendId);
  },
  createFriendship: (userId: string, friendId: string) => {
    if (!db.friendships[userId]) db.friendships[userId] = [];
    if (!db.friendships[friendId]) db.friendships[friendId] = [];
    
    if (db.friendships[userId].some((f: any) => f.friend_id === friendId)) {
      return null;
    }

    const newFriendship1 = {
      id: Math.random().toString(36).substring(2, 11),
      user_id: userId,
      friend_id: friendId,
      status: 'accepted',
      created_at: new Date().toISOString()
    };
    db.friendships[userId].push(newFriendship1);
    
    const newFriendship2 = {
      id: Math.random().toString(36).substring(2, 11),
      user_id: friendId,
      friend_id: userId,
      status: 'accepted',
      created_at: new Date().toISOString()
    };
    db.friendships[friendId].push(newFriendship2);
    
    saveDb();
    return newFriendship1;
  },

  // Challenges Methods
  getChallenges: () => {
    return db.challenges || [];
  },
  getUserChallenges: (userId: string) => {
    const list = db.userChallenges[userId] || [];
    return list.map(uc => {
      const challenge = db.challenges.find(c => c.id === uc.challenge_id);
      return {
        ...uc,
        challenge
      };
    });
  },
  joinChallenge: (userId: string, challengeId: string) => {
    if (!db.userChallenges[userId]) db.userChallenges[userId] = [];
    if (db.userChallenges[userId].some(uc => uc.challenge_id === challengeId)) {
      return db.userChallenges[userId].find(uc => uc.challenge_id === challengeId);
    }
    const newUC = {
      id: Math.random().toString(36).substring(2, 11),
      user_id: userId,
      challenge_id: challengeId,
      completed_workouts: 2,
      completed: false,
      joined_at: new Date().toISOString()
    };
    db.userChallenges[userId].push(newUC);
    saveDb();
    return newUC;
  },
  updateChallengeProgress: (userId: string, challengeId: string) => {
    if (!db.userChallenges[userId]) return null;
    const uc = db.userChallenges[userId].find(u => u.challenge_id === challengeId);
    if (uc) {
      const challenge = db.challenges.find(c => c.id === challengeId);
      const target = challenge ? challenge.target_workouts : 5;
      uc.completed_workouts = Math.min(target, uc.completed_workouts + 1);
      if (uc.completed_workouts >= target) {
        uc.completed = true;
      }
      saveDb();
    }
    return uc;
  },
  
  // Weekly points aggregation helper for Leaderboard
  getWeeklyPoints: (userId: string) => {
    const todayStr = new Date().toISOString().split('T')[0];
    const stats = fallbackDb.getDailyStats(userId, todayStr);
    const workouts = db.workouts[userId] || [];
    const workoutsCount = workouts.length;
    const points = Math.round((stats.steps || 0) * 0.1 + (stats.water_ml || 0) * 0.05 + workoutsCount * 100);
    return points || 0;
  }
};
