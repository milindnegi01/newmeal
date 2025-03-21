from fastapi import FastAPI, HTTPException
import requests
import os
import asyncpg
import random
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import asyncio


# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Supabase Database Credentials
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
MEALDB_API_URL = "https://www.themealdb.com/api/json/v1/1/search.php?s="

# Async function to connect to Supabase PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


# API Endpoint to fetch meal details
@app.get("/meals/{meal_name}")
async def get_meal(meal_name: str):
    MAX_RESULTS = 20
    mealdb_meals = []
    supabase_meals = []

    # Step 1: Check in MealDB
    try:
        mealdb_response = requests.get(f"{MEALDB_API_URL}{meal_name}")
        if mealdb_response.status_code == 200:
            mealdb_data = mealdb_response.json()
            if mealdb_data["meals"]:
                for meal in mealdb_data["meals"]:
                    meal["source"] = "MealDB"
                    mealdb_meals.append(meal)
    except Exception as e:
        print(f"MealDB API error: {str(e)}")  # Log the error but continue

    # Step 2: Check in Supabase Database
    try:
        conn = await get_db_connection()
        
        db_meals = await conn.fetch("""
            SELECT *, 
                CASE WHEN LOWER(name) = LOWER($1) THEN 1 ELSE 2 END as match_priority
            FROM extra_meals 
            WHERE LOWER(name) LIKE LOWER($2)
            ORDER BY match_priority ASC
        """, meal_name, f"%{meal_name}%")
        
        await conn.close()
        
        if db_meals:
            for meal in db_meals:
                formatted_meal = {
                    "idMeal": meal["id"],
                    "strMeal": meal["name"],
                    "strCategory": meal["category"],
                    "strArea": meal["area"],
                    "strInstructions": meal["instructions"].split("', '"),
                    "strMealThumb": meal["image"],
                    "strIngredients": meal["ingredients"].strip("[]").replace("'", "").split(", ") if meal["ingredients"] else [],
                    "source": "Supabase DB"
                }
                supabase_meals.append(formatted_meal)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not mealdb_meals and not supabase_meals:
        raise HTTPException(status_code=404, detail="Meal not found in MealDB or Supabase database.")

    # Balanced random selection
    final_meals = []
    total_meals_needed = MAX_RESULTS

    if mealdb_meals and supabase_meals:
        # Calculate balanced proportions
        mealdb_proportion = min(len(mealdb_meals), total_meals_needed // 2)
        supabase_proportion = total_meals_needed - mealdb_proportion

        # Random selection from MealDB
        if len(mealdb_meals) > mealdb_proportion:
            final_meals.extend(random.sample(mealdb_meals, mealdb_proportion))
        else:
            final_meals.extend(mealdb_meals)

        # Random selection from Supabase
        if len(supabase_meals) > supabase_proportion:
            final_meals.extend(random.sample(supabase_meals, supabase_proportion))
        else:
            final_meals.extend(supabase_meals)

    else:
        # If we only have results from one source, use those
        source_meals = mealdb_meals if mealdb_meals else supabase_meals
        final_meals = random.sample(source_meals, min(len(source_meals), total_meals_needed))

    # Shuffle the final list to mix results from both sources
    random.shuffle(final_meals)

    # Return combined results
    return {
        "total_available": len(mealdb_meals) + len(supabase_meals),
        "mealdb_count": len(mealdb_meals),
        "supabase_count": len(supabase_meals),
        "returned_results": len(final_meals),
        "max_results": MAX_RESULTS,
        "data": final_meals
    }

# API Endpoint to add a meal to the database
@app.post("/add_meal/")
async def add_meal(name: str, category: str, area: str, instructions: str, ingredients: str, image: str):
    try:
        conn = await get_db_connection()
        await conn.execute(
            "INSERT INTO extra_meals (name, category, area, instructions, ingredients, image) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (name) DO NOTHING",
            name, category, area, instructions, ingredients, image
        )
        await conn.close()
        return {"message": "Meal added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
