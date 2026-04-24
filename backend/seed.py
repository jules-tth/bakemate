import asyncio
from sqlmodel import Session, select

from app.models.user import User, UserCreate
from app.models.recipe import Recipe, RecipeCreate
from app.services.user_service import UserService
from app.repositories.sqlite_adapter import engine

async def seed_data():
    with Session(engine) as session:
        user_service = UserService(session)

        # Check if the default test user already exists.
        user = session.exec(
            select(User).where(User.email == "test@example.com")
        ).first()
        if user:
            print("Database already seeded.")
            return

        # Create a user
        user_in = UserCreate(email="test@example.com", password="password")
        user = await user_service.create_user(user_in)

        # Create recipes for the user
        recipes_data = [
            {
                "name": "Classic Chocolate Chip Cookies",
                "description": "The best chocolate chip cookies ever!",
                "user_id": user.id,
                "steps": "1. Preheat oven to 375°F (190°C). 2. Cream together butter, white sugar, and brown sugar until smooth. 3. Beat in the eggs one at a time, then stir in the vanilla. 4. Dissolve baking soda in hot water. Add to batter along with salt. 5. Stir in flour, chocolate chips, and nuts. 6. Drop by large spoonfuls onto ungreased pans. 7. Bake for about 10 minutes in the preheated oven, or until edges are nicely browned."
            },
            {
                "name": "Sourdough Bread",
                "description": "A crusty, chewy sourdough bread.",
                "user_id": user.id,
                "steps": "1. Feed your sourdough starter. 2. Mix the dough. 3. Bulk ferment. 4. Shape the dough. 5. Cold ferment. 6. Bake the bread."
            },
            {
                "name": "New York-Style Pizza",
                "description": "A classic New York-style pizza with a thin, crisp crust.",
                "user_id": user.id,
                "steps": "1. Make the dough. 2. Make the sauce. 3. Assemble the pizza. 4. Bake the pizza."
            },
        ]

        for recipe_data in recipes_data:
            recipe_in = RecipeCreate(**recipe_data)
            session.add(Recipe(**recipe_in.model_dump()))

        session.commit()
        print("Database seeded with a user and recipes.")
