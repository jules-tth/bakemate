import pytest
from unittest.mock import MagicMock, patch
from app.models.recipe import Recipe
from app.models.ingredient import Ingredient

# Mock the calculate_recipe_cost function to avoid dependency on the actual implementation
@pytest.fixture
def mock_calculate_recipe_cost():
    with patch('app.services.recipe_service.calculate_recipe_cost') as mock:
        mock.return_value = 9.47
        yield mock

def test_recipe_model_basic():
    """Test basic Recipe model functionality."""
    # Create a recipe
    recipe = Recipe(
        name="Test Recipe",
        description="A test recipe description",
        instructions="Mix and bake",
        prep_time=30,
        cook_time=45
    )
    
    # Verify attributes
    assert recipe.name == "Test Recipe"
    assert recipe.description == "A test recipe description"
    assert recipe.instructions == "Mix and bake"
    assert recipe.prep_time == 30
    assert recipe.cook_time == 45
    
    # Verify total time calculation
    assert recipe.total_time == 75

def test_ingredient_model_basic():
    """Test basic Ingredient model functionality."""
    # Create an ingredient
    ingredient = Ingredient(
        name="Test Ingredient",
        description="A test ingredient",
        unit_cost=2.99,
        stock_quantity=100,
        unit="cup"
    )
    
    # Verify attributes
    assert ingredient.name == "Test Ingredient"
    assert ingredient.description == "A test ingredient"
    assert ingredient.unit_cost == 2.99
    assert ingredient.stock_quantity == 100
    assert ingredient.unit == "cup"

def test_ingredient_low_stock_warning():
    """Test ingredient low stock warning functionality."""
    # Create an ingredient with low stock
    ingredient = Ingredient(
        name="Low Stock Item",
        description="An item with low stock",
        unit_cost=5.99,
        stock_quantity=3,
        unit="piece",
        low_stock_threshold=5
    )
    
    # Verify low stock warning
    assert ingredient.is_low_stock() == True
    
    # Create an ingredient with sufficient stock
    ingredient = Ingredient(
        name="Sufficient Stock Item",
        description="An item with sufficient stock",
        unit_cost=5.99,
        stock_quantity=10,
        unit="piece",
        low_stock_threshold=5
    )
    
    # Verify no low stock warning
    assert ingredient.is_low_stock() == False
