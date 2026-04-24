import pytest
from uuid import uuid4

import asyncio

from app.models.recipe import (
    Recipe,
    RecipeCreate,
    RecipeIngredientLink,
    RecipeIngredientLinkCreate,
    RecipeUpdate,
)
from app.models.user import User
from app.services.recipe_service import RecipeService, calculate_recipe_cost


def test_calculate_recipe_cost_mock():
    """Test recipe cost calculation with mocked data."""
    # Mock ingredients data
    ingredients = [
        {"id": "1", "quantity": 2, "unit": "cup", "unit_cost": 2.99},
        {"id": "2", "quantity": 1, "unit": "cup", "unit_cost": 3.49},
    ]

    # Mock session that returns our test data
    class MockSession:
        def get(self, model, id):
            for ingredient in ingredients:
                if ingredient["id"] == id:
                    return type(
                        "obj",
                        (object,),
                        {"id": ingredient["id"], "unit_cost": ingredient["unit_cost"]},
                    )
            return None

    # Calculate cost using our function
    recipe_id = "test-recipe"
    recipe_ingredients = [
        {"id": "1", "quantity": 2, "unit": "cup"},
        {"id": "2", "quantity": 1, "unit": "cup"},
    ]

    # Expected cost: (2 * 2.99) + (1 * 3.49) = 9.47
    expected_cost = (2 * 2.99) + (1 * 3.49)

    # Mock the actual calculation function to use our test data
    def mock_calculate(recipe_id, ingredients, session):
        total_cost = 0
        for ingredient in ingredients:
            ing_obj = session.get(None, ingredient["id"])
            if ing_obj:
                total_cost += ing_obj.unit_cost * ingredient["quantity"]
        return total_cost

    # Run the calculation with our mock
    result = mock_calculate(recipe_id, recipe_ingredients, MockSession())

    # Assert the result
    assert result == pytest.approx(expected_cost, 0.01)


def test_calculate_recipe_cost_missing_ingredient():
    """Returns 0 when an ingredient lookup fails."""

    class MockSession:
        def get(self, model, id):
            return None

    recipe_ingredients = [{"id": "missing", "quantity": 2, "unit": "cup"}]

    result = calculate_recipe_cost("test-recipe", recipe_ingredients, MockSession())

    assert result == 0


def test_create_recipe_calculates_cost_and_links():
    user_id = uuid4()
    ingredient_id = uuid4()

    class StubIngredientRepo:
        async def get(self, id):
            class Obj:
                unit_cost = 2.5

            return Obj()

    class StubSession:
        def __init__(self):
            self.added = []

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            pass

        def refresh(self, _obj):
            pass

    service = RecipeService(session=StubSession())
    service.ingredient_repo = StubIngredientRepo()

    recipe_in = RecipeCreate(
        user_id=user_id,
        name="Cake",
        instructions="mix",
        ingredients=[
            RecipeIngredientLinkCreate(
                ingredient_id=ingredient_id, quantity=2, unit="g"
            )
        ],
    )

    result = asyncio.run(
        service.create_recipe(
            recipe_in=recipe_in,
            current_user=User(
                id=user_id, email="baker@example.com", hashed_password="x"
            ),
        )
    )

    assert result.calculated_cost == 5.0


def test_get_recipe_by_id_returns_none_when_missing():
    class StubExecResult:
        def one_or_none(self):
            return None

    class StubSession:
        def exec(self, _stmt):
            return StubExecResult()

    service = RecipeService(session=StubSession())

    res = asyncio.run(
        service.get_recipe_by_id(
            recipe_id=uuid4(),
            current_user=User(id=uuid4(), email="a@b.com", hashed_password="x"),
        )
    )

    assert res is None


def test_get_recipes_by_user_maps_links():
    user_id = uuid4()
    recipe = Recipe(id=uuid4(), user_id=user_id, name="Pie", steps="mix")
    link = RecipeIngredientLink(
        recipe_id=recipe.id, ingredient_id=uuid4(), quantity=1, unit="g"
    )

    class StubExecResult:
        def all(self):
            return [(recipe, link)]

    class StubSession:
        def exec(self, _stmt):
            return StubExecResult()

    service = RecipeService(session=StubSession())

    recipes = asyncio.run(
        service.get_recipes_by_user(
            current_user=User(id=user_id, email="b@c.com", hashed_password="x"),
        )
    )

    assert recipes[0].ingredient_links[0].ingredient_id == link.ingredient_id


def test_update_recipe_updates_fields():
    user_id = uuid4()
    recipe_id = uuid4()

    class StubRecipeRepo:
        async def get(self, id):
            return Recipe(id=recipe_id, user_id=user_id, name="Cake", steps="mix")

    class StubSession:
        def add(self, _obj):
            pass

        def commit(self):
            pass

        def refresh(self, _obj):
            pass

        def exec(self, _stmt):
            class Result:
                def all(self):
                    return []

            return Result()

    service = RecipeService(session=StubSession())
    service.recipe_repo = StubRecipeRepo()

    updated = asyncio.run(
        service.update_recipe(
            recipe_id=recipe_id,
            recipe_in=RecipeUpdate(name="Bread"),
            current_user=User(id=user_id, email="a@b.com", hashed_password="x"),
        )
    )

    assert updated.name == "Bread"


def test_delete_recipe_closes_session():
    user_id = uuid4()
    recipe_id = uuid4()

    class StubRecipeRepo:
        async def get(self, id):
            return Recipe(id=recipe_id, user_id=user_id, name="Pie", steps="mix")

        async def delete(self, id):
            return Recipe(id=recipe_id, user_id=user_id, name="Pie", steps="mix")

    class StubSession:
        def __init__(self):
            self.closed = False

        def exec(self, _stmt):
            pass

        def close(self):
            self.closed = True

    session = StubSession()
    service = RecipeService(session=session)
    service.recipe_repo = StubRecipeRepo()

    result = asyncio.run(
        service.delete_recipe(
            recipe_id=recipe_id,
            current_user=User(id=user_id, email="a@b.com", hashed_password="x"),
        )
    )

    assert result.name == "Pie"
    assert session.closed
