from fastapi import FastAPI, HTTPException
import httpx
import os
import asyncpg
import random
import asyncio
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
<<<<<<< HEAD

# Basic setup
print("🟢 Starting application initialization...")
app = FastAPI()
=======
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("SUPABASE_DB_URL")
MEALDB_API_URL = "https://www.themealdb.com/api/json/v1/1/search.php?s="
MAX_RESULTS = 20

# Database pool
db_pool = None

# Startup and shutdown events manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database pool
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            timeout=30
        )
        print("Database pool created successfully")
    except Exception as e:
        print(f"Failed to create database pool: {str(e)}")
        raise

    yield

    # Shutdown: Close database pool
    if db_pool:
        await db_pool.close()
        print("Database pool closed")

app = FastAPI(lifespan=lifespan)
>>>>>>> 571dd7b428e124ec8b3c854ffb8e98ca8c2fd092

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# Load environment variables
print("📌 Loading environment variables...")
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("SUPABASE_DB_URL")
MEALDB_API_URL = "https://www.themealdb.com/api/json/v1/1/search.php?s="
MAX_RESULTS = 20

# Global database pool
db_pool = None

# Startup event
@app.on_event("startup")
async def startup():
    global db_pool
    print("🟢 App is starting...")

    if not DATABASE_URL:
        print("🔴 ERROR: No database URL found! Check Render environment variables.")
        return

    try:
        print("🔄 Connecting to database...")
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            ssl="require"
        )
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        db_pool = None  # Prevent app crash

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()
        print("🔴 Database pool closed")

# Health check endpoint
@app.get("/")
async def root():
    return {"status": "online", "message": "API is running"}

@app.get("/health")
async def health_check():
    if not db_pool:
        return {"status": "error", "message": "No database pool"}
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def fetch_mealdb_meals(meal_name: str) -> list:
    """Asynchronously fetch meals from MealDB API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MEALDB_API_URL}{meal_name}")
            response.raise_for_status()
            data = response.json()
            if data.get("meals"):
                return [{**meal, "source": "MealDB"} for meal in data["meals"]]
    except Exception as e:
        print(f"❌ MealDB API error: {str(e)}")
    return []

async def fetch_supabase_meals(meal_name: str) -> list:
    """Fetch meals from Supabase database"""
    try:
        if not db_pool:
            print("⚠️ Database pool not available")
            return []
=======
async def fetch_mealdb_meals(meal_name: str) -> list:
    """Asynchronously fetch meals from MealDB API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MEALDB_API_URL}{meal_name}")
            response.raise_for_status()
            data = response.json()
            if data.get("meals"):
                return [{**meal, "source": "MealDB"} for meal in data["meals"]]
    except Exception as e:
        print(f"MealDB API error: {str(e)}")
    return []

async def fetch_supabase_meals(meal_name: str) -> list:
    """Fetch meals from Supabase database"""
    try:
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection not available")
>>>>>>> 571dd7b428e124ec8b3c854ffb8e98ca8c2fd092
            
        async with db_pool.acquire() as conn:
            meals = await conn.fetch("""
                SELECT *, 
                    CASE WHEN LOWER(name) = LOWER($1) THEN 1 ELSE 2 END as match_priority
                FROM extra_meals 
                WHERE LOWER(name) LIKE LOWER($2)
                ORDER BY match_priority ASC
            """, meal_name, f"%{meal_name}%")

            return [
                {
                    "idMeal": str(meal["id"]),
                    "strMeal": meal["name"],
                    "strCategory": meal["category"],
                    "strArea": meal["area"],
                    "strInstructions": meal["instructions"],
                    "strMealThumb": meal["images"],
                    "strIngredients": meal["ingredients"].strip("[]").replace("'", "").split(", ") if meal["ingredients"] else [],
                    "minutes": meal["minutes"],
                    "source": "Supabase DB"
                }
                for meal in meals
            ]
<<<<<<< HEAD
    except Exception as e:
        print(f"❌ Supabase error: {str(e)}")
        return []

@app.get("/meals/{meal_name}")
async def get_meal(meal_name: str):
    """Get meals from both sources and return balanced results"""
    try:
        if not meal_name or len(meal_name.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")

        print(f"🔍 Searching for: {meal_name}")

        # Fetch from both sources concurrently
        mealdb_meals, supabase_meals = await asyncio.gather(
            fetch_mealdb_meals(meal_name),
            fetch_supabase_meals(meal_name),
            return_exceptions=True
        )

        # Check for exceptions in results
        if isinstance(mealdb_meals, Exception):
            print(f"⚠️ MealDB error: {str(mealdb_meals)}")
            mealdb_meals = []
        if isinstance(supabase_meals, Exception):
            print(f"⚠️ Supabase error: {str(supabase_meals)}")
            supabase_meals = []

        print(f"📊 MealDB results: {len(mealdb_meals)}, Supabase results: {len(supabase_meals)}")

        if not mealdb_meals and not supabase_meals:
            return {
                "total_available": 0,
                "mealdb_count": 0,
                "supabase_count": 0,
                "returned_results": 0,
                "max_results": MAX_RESULTS,
                "data": []
            }

        # Balanced random selection
        final_meals = []
        if mealdb_meals and supabase_meals:
            mealdb_proportion = min(len(mealdb_meals), MAX_RESULTS // 2)
            supabase_proportion = MAX_RESULTS - mealdb_proportion

            if len(mealdb_meals) > mealdb_proportion:
                final_meals.extend(random.sample(mealdb_meals, mealdb_proportion))
            else:
                final_meals.extend(mealdb_meals)

            if len(supabase_meals) > supabase_proportion:
                final_meals.extend(random.sample(supabase_meals, supabase_proportion))
            else:
                final_meals.extend(supabase_meals)
        else:
            source_meals = mealdb_meals if mealdb_meals else supabase_meals
            final_meals = random.sample(source_meals, min(len(source_meals), MAX_RESULTS))

        random.shuffle(final_meals)

        return {
            "total_available": len(mealdb_meals) + len(supabase_meals),
            "mealdb_count": len(mealdb_meals),
            "supabase_count": len(supabase_meals),
            "returned_results": len(final_meals),
            "max_results": MAX_RESULTS,
            "data": final_meals
        }
=======
    except Exception as e:
        print(f"Supabase error: {str(e)}")
        return []

@app.get("/meals/{meal_name}")
async def get_meal(meal_name: str):
    """Get meals from both sources and return balanced results"""
    try:
        if not meal_name or len(meal_name.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")

        print(f"Searching for: {meal_name}")

        # Fetch from both sources concurrently
        mealdb_meals, supabase_meals = await asyncio.gather(
            fetch_mealdb_meals(meal_name),
            fetch_supabase_meals(meal_name),
            return_exceptions=True
        )

        # Check for exceptions in results
        if isinstance(mealdb_meals, Exception):
            print(f"MealDB error: {str(mealdb_meals)}")
            mealdb_meals = []
        if isinstance(supabase_meals, Exception):
            print(f"Supabase error: {str(supabase_meals)}")
            supabase_meals = []

        print(f"MealDB results: {len(mealdb_meals)}")
        print(f"Supabase results: {len(supabase_meals)}")

        if not mealdb_meals and not supabase_meals:
            return {
                "total_available": 0,
                "mealdb_count": 0,
                "supabase_count": 0,
                "returned_results": 0,
                "max_results": MAX_RESULTS,
                "data": []
            }

        # Balanced random selection
        final_meals = []
        if mealdb_meals and supabase_meals:
            mealdb_proportion = min(len(mealdb_meals), MAX_RESULTS // 2)
            supabase_proportion = MAX_RESULTS - mealdb_proportion

            if len(mealdb_meals) > mealdb_proportion:
                final_meals.extend(random.sample(mealdb_meals, mealdb_proportion))
            else:
                final_meals.extend(mealdb_meals)

            if len(supabase_meals) > supabase_proportion:
                final_meals.extend(random.sample(supabase_meals, supabase_proportion))
            else:
                final_meals.extend(supabase_meals)
        else:
            source_meals = mealdb_meals if mealdb_meals else supabase_meals
            final_meals = random.sample(source_meals, min(len(source_meals), MAX_RESULTS))

        random.shuffle(final_meals)

        return {
            "total_available": len(mealdb_meals) + len(supabase_meals),
            "mealdb_count": len(mealdb_meals),
            "supabase_count": len(supabase_meals),
            "returned_results": len(final_meals),
            "max_results": MAX_RESULTS,
            "data": final_meals
        }

    except Exception as e:
        print(f"Error in get_meal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_meal/")
async def add_meal(
    name: str, 
    category: str = "Unknown", 
    area: str = "Unknown", 
    instructions: str = "", 
    ingredients: str = "", 
    images: str = "",
    minutes: int = 0
):
    """Add a new meal to the database"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database connection not available")
        
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO extra_meals 
                (name, category, area, instructions, ingredients, images, minutes) 
                VALUES ($1, $2, $3, $4, $5, $6, $7) 
                ON CONFLICT (name) DO NOTHING
            """, name, category, area, instructions, ingredients, images, minutes)
            
        return {"message": "Meal added successfully"}
>>>>>>> 571dd7b428e124ec8b3c854ffb8e98ca8c2fd092

    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="Meal already exists")
    except Exception as e:
<<<<<<< HEAD
        print(f"❌ Error in get_meal: {str(e)}")
=======
        print(f"Error adding meal: {str(e)}")
>>>>>>> 571dd7b428e124ec8b3c854ffb8e98ca8c2fd092
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
<<<<<<< HEAD
    port = int(os.getenv("PORT", 8000))  # Use Render's dynamic port
    uvicorn.run("main:app", host="0.0.0.0", port=port)
=======
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
>>>>>>> 571dd7b428e124ec8b3c854ffb8e98ca8c2fd092
