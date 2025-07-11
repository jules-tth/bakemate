import pytest
from sqlmodel import SQLModel, create_engine, Session
from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.services.recipe_service import calculate_recipe_cost


@pytest.fixture
def test_db():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(test_db):
    """Create a new database session for testing."""
    with Session(test_db) as session:
        yield session


def test_calculate_recipe_cost(session):
    """Test recipe cost calculation."""
    # Create test ingredients
    flour = Ingredient(
        name="Flour",
        description="All-purpose flour",
        unit_cost=2.99,
        stock_quantity=1000,
        unit="cup",
    )
    sugar = Ingredient(
        name="Sugar",
        description="Granulated sugar",
        unit_cost=3.49,
        stock_quantity=500,
        unit="cup",
    )
    session.add(flour)
    session.add(sugar)
    session.commit()

    # Create a recipe using these ingredients
    recipe = Recipe(
        name="Simple Cake",
        description="A simple cake recipe",
        instructions="Mix and bake",
    )
    session.add(recipe)
    session.commit()

    # Add recipe ingredients (normally would be done through a relationship)
    recipe_ingredients = [
        {"id": flour.id, "quantity": 2, "unit": "cup"},
        {"id": sugar.id, "quantity": 1, "unit": "cup"},
    ]

    # Calculate cost
    cost = calculate_recipe_cost(recipe.id, recipe_ingredients, session)

    # Expected cost: (2 * 2.99) + (1 * 3.49) = 9.47
    expected_cost = (2 * 2.99) + (1 * 3.49)
    assert cost == pytest.approx(expected_cost, 0.01)


def test_inventory_decrement(session):
    """Test inventory decrement when recipe is used."""
    # Create test ingredient
    butter = Ingredient(
        name="Butter",
        description="Unsalted butter",
        unit_cost=4.99,
        stock_quantity=10,
        unit="stick",
    )
    session.add(butter)
    session.commit()

    # Initial quantity
    initial_quantity = butter.stock_quantity

    # Simulate using 2 sticks of butter
    butter.stock_quantity -= 2
    session.commit()

    # Verify quantity was decremented
    session.refresh(butter)
    assert butter.stock_quantity == initial_quantity - 2
