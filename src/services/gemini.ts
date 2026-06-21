import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';
dotenv.config();

// Ensure the API key is provided
const apiKey = process.env.GEMINI_API_KEY || '';

if (!apiKey || apiKey === 'your_gemini_api_key_here') {
  console.warn('WARNING: GEMINI_API_KEY is not set or is using the placeholder. Offline simulated fallbacks will be used.');
}

// Fallback to placeholder key to allow server startup (e.g. for health checks) without throwing runtime crash.
const genAI = new GoogleGenerativeAI(apiKey && apiKey !== 'your_gemini_api_key_here' ? apiKey : 'placeholder-gemini-key');

const isApiKeyPlaceholder = () => {
  return !apiKey || 
         apiKey === 'your_gemini_api_key_here' || 
         apiKey === 'placeholder-gemini-key' || 
         apiKey.trim() === '';
};

// Realistic mock meals fallback pool
const mealFallbacks = [
  { name: "Avocado Toast with Poached Eggs", calories: 380, protein: 16, carbs: 32, fats: 20 },
  { name: "Grilled Chicken & Quinoa Salad", calories: 480, protein: 38, carbs: 42, fats: 14 },
  { name: "Pan-Seared Salmon with Broccoli", calories: 520, protein: 42, carbs: 12, fats: 34 },
  { name: "Greek Yogurt with Berries & Honey", calories: 240, protein: 18, carbs: 28, fats: 4 },
  { name: "Whey Protein Shake with Banana", calories: 310, protein: 28, carbs: 44, fats: 3 }
];

const getRandomMealFallback = () => {
  const idx = Math.floor(Math.random() * mealFallbacks.length);
  return mealFallbacks[idx];
};

// Fallback parser for text descriptions
const parseTextFallback = (description: string) => {
  const desc = description.toLowerCase();
  
  if (desc.includes("chicken")) {
    return { name: "Grilled Chicken Breast with Rice", calories: 450, protein: 35, carbs: 40, fats: 8 };
  }
  if (desc.includes("salmon") || desc.includes("fish")) {
    return { name: "Seared Salmon & Asparagus", calories: 510, protein: 38, carbs: 10, fats: 32 };
  }
  if (desc.includes("egg") || desc.includes("eggs") || desc.includes("omelette")) {
    return { name: "Scrambled Eggs with Toast", calories: 320, protein: 16, carbs: 24, fats: 16 };
  }
  if (desc.includes("shake") || desc.includes("protein shake") || desc.includes("whey")) {
    return { name: "Whey Protein Shake", calories: 160, protein: 25, carbs: 3, fats: 2 };
  }
  if (desc.includes("banana")) {
    return { name: "Fresh Banana", calories: 105, protein: 1, carbs: 27, fats: 0 };
  }
  if (desc.includes("apple")) {
    return { name: "Fresh Apple", calories: 95, protein: 0, carbs: 25, fats: 0 };
  }
  if (desc.includes("salad")) {
    return { name: "Mixed Green Salad with Vinaigrette", calories: 150, protein: 2, carbs: 12, fats: 10 };
  }
  if (desc.includes("coffee")) {
    return { name: "Black Coffee / Americano", calories: 5, protein: 0, carbs: 0, fats: 0 };
  }
  if (desc.includes("rice")) {
    return { name: "Steamed White Rice", calories: 200, protein: 4, carbs: 45, fats: 0 };
  }
  if (desc.includes("avocado")) {
    return { name: "Avocado Toast", calories: 290, protein: 6, carbs: 24, fats: 18 };
  }

  const cleanName = description.trim().replace(/^\w/, (c) => c.toUpperCase());
  return {
    name: cleanName,
    calories: 350,
    protein: 15,
    carbs: 45,
    fats: 12
  };
};

export const analyzeMealImage = async (mimeType: string, base64Image: string) => {
  if (isApiKeyPlaceholder()) {
    console.warn("Using offline simulated fallback for analyzeMealImage due to missing/placeholder GEMINI_API_KEY.");
    return getRandomMealFallback();
  }

  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  const prompt = `Analyze this food image. Provide a highly accurate estimation of:
  1. The name of the dish
  2. Total Calories
  3. Macros: Protein (g), Carbs (g), Fats (g)
  Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text.`;

  const imageParts = [
    {
      inlineData: {
        data: base64Image,
        mimeType
      }
    }
  ];

  try {
    const result = await model.generateContent([prompt, ...imageParts]);
    const response = await result.response;
    const text = response.text();
    const cleanedText = text.replace(/```json/g, '').replace(/```/g, '').trim();
    return JSON.parse(cleanedText);
  } catch (error) {
    console.error("Gemini API Error (falling back to simulation):", error);
    return getRandomMealFallback();
  }
};

export const generateMockMeal = async () => {
  if (isApiKeyPlaceholder()) {
    return getRandomMealFallback();
  }

  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  const prompt = `Generate a realistic, healthy meal choice suitable for a fitness tracking application (e.g., Avocado Toast, Salmon Salad, Chicken Protein Bowl, Greek Yogurt with Berries, etc.) and estimate its nutritional values.
  Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text.`;

  try {
    const result = await model.generateContent([prompt]);
    const response = await result.response;
    const text = response.text();
    const cleanedText = text.replace(/```json/g, '').replace(/```/g, '').trim();
    return JSON.parse(cleanedText);
  } catch (error) {
    console.error("Gemini Mock Meal Error (falling back to simulation):", error);
    return getRandomMealFallback();
  }
};

export const analyzeMealText = async (description: string) => {
  if (isApiKeyPlaceholder()) {
    console.warn("Using offline simulated fallback for analyzeMealText due to missing/placeholder GEMINI_API_KEY.");
    return parseTextFallback(description);
  }

  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  const prompt = `Analyze this food description: "${description}". Provide a highly accurate estimation of:
  1. The name of the dish
  2. Total Calories
  3. Macros: Protein (g), Carbs (g), Fats (g)
  Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text.`;

  try {
    const result = await model.generateContent([prompt]);
    const response = await result.response;
    const text = response.text();
    const cleanedText = text.replace(/```json/g, '').replace(/```/g, '').trim();
    return JSON.parse(cleanedText);
  } catch (error) {
    console.error("Gemini Text API Error (falling back to simulation):", error);
    return parseTextFallback(description);
  }
};

export const analyzeMealLabel = async (mimeType: string, base64Image: string) => {
  if (isApiKeyPlaceholder()) {
    console.warn("Using offline simulated fallback for analyzeMealLabel due to missing/placeholder GEMINI_API_KEY.");
    return {
      name: "Nutrition Label Scan",
      calories: 220,
      protein: 12,
      carbs: 28,
      fats: 6
    };
  }

  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  const prompt = `Analyze this nutrition label image. Extract:
  1. The product name (or a descriptive name based on the label/packaging)
  2. Calories per serving
  3. Macros: Protein (g), Carbs (g), Fats (g) per serving
  Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text.`;

  const imageParts = [
    {
      inlineData: {
        data: base64Image,
        mimeType
      }
    }
  ];

  try {
    const result = await model.generateContent([prompt, ...imageParts]);
    const response = await result.response;
    const text = response.text();
    const cleanedText = text.replace(/```json/g, '').replace(/```/g, '').trim();
    return JSON.parse(cleanedText);
  } catch (error) {
    console.error("Gemini Label API Error (falling back to simulation):", error);
    return {
      name: "Nutrition Label Scan",
      calories: 220,
      protein: 12,
      carbs: 28,
      fats: 6
    };
  }
};

export const analyzeMealBarcode = async (barcode: string) => {
  if (isApiKeyPlaceholder()) {
    return {
      name: `Scanned Product (${barcode})`,
      calories: 180,
      protein: 10,
      carbs: 22,
      fats: 6
    };
  }

  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  const prompt = `Provide estimated nutrition facts (calories, protein, carbs, fats) for the product with UPC/barcode or name: "${barcode}". If the barcode format is standard, estimate the realistic food item.
  Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text.`;

  try {
    const result = await model.generateContent([prompt]);
    const response = await result.response;
    const text = response.text();
    const cleanedText = text.replace(/```json/g, '').replace(/```/g, '').trim();
    return JSON.parse(cleanedText);
  } catch (error) {
    console.error("Gemini Barcode API Error (falling back to simulation):", error);
    return {
      name: `Scanned Product (${barcode})`,
      calories: 180,
      protein: 10,
      carbs: 22,
      fats: 6
    };
  }
};

export const generateWorkoutInsight = async (workouts: any[], dailyStats: any) => {
  if (isApiKeyPlaceholder()) {
    return "Consistency is the secret ingredient! Keep logging your daily tasks to reach your goals.";
  }

  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  const prompt = `Based on the following user data:
Workouts: ${JSON.stringify(workouts.slice(0, 5))}
Daily Stats: ${JSON.stringify(dailyStats)}
Provide a short, motivating, and highly personalized 1-sentence AI insight about their progress. Don't use quotes.`;

  try {
    const result = await model.generateContent([prompt]);
    const response = await result.response;
    return response.text().trim();
  } catch (error) {
    console.error("Gemini Insight API Error (falling back to simulation):", error);
    return "Keep up the great work! Consistency is the key to your success.";
  }
};
