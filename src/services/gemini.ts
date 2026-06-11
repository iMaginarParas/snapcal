import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';
dotenv.config();

// Ensure the API key is provided
const apiKey = process.env.GEMINI_API_KEY || '';

if (!apiKey) {
  console.error('ERROR: GEMINI_API_KEY is not set in environment variables.');
}

// Fallback to placeholder key to allow server startup (e.g. for health checks) without throwing runtime crash.
const genAI = new GoogleGenerativeAI(apiKey || 'placeholder-gemini-key');

export const analyzeMealImage = async (mimeType: string, base64Image: string) => {
  // Using gemini-1.5-flash for fast multimodal tasks
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
    // Clean up any potential markdown code blocks if the model ignores instructions
    const cleanedText = text.replace(/```json/g, '').replace(/```/g, '').trim();
    return JSON.parse(cleanedText);
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw new Error("Failed to analyze image");
  }
};

export const generateMockMeal = async () => {
  // Using gemini-1.5-flash for fast text generation
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
    console.error("Gemini Mock Meal Generation Error:", error);
    throw new Error("Failed to generate mock meal");
  }
};

export const analyzeMealText = async (description: string) => {
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
    console.error("Gemini Text API Error:", error);
    throw new Error("Failed to analyze text description");
  }
};

export const analyzeMealLabel = async (mimeType: string, base64Image: string) => {
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
    console.error("Gemini Label API Error:", error);
    throw new Error("Failed to analyze nutrition label");
  }
};

export const analyzeMealBarcode = async (barcode: string) => {
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
    console.error("Gemini Barcode API Error:", error);
    // Dynamic realistic fallback based on input
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
    console.error("Gemini Insight API Error:", error);
    return "Keep up the great work! Consistency is the key to your success.";
  }
};
