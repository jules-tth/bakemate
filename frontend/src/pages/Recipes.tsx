import { FormEvent, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listRecipes, createRecipe } from '../api/recipes';
import type { Recipe } from '../api/recipes';

export default function Recipes() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [form, setForm] = useState({ name: '', description: '' });

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        const data = await listRecipes();
        setRecipes(data);
      } catch (error) {
        console.error(error);
      }
    };

    fetchRecipes();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const newRecipe = await createRecipe({
        name: form.name,
        description: form.description,
      });
      setRecipes((prev) => [...prev, newRecipe]);
      setForm({ name: '', description: '' });
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h2 className="mb-6 text-2xl font-semibold text-gray-700">Your Recipes</h2>

      <form onSubmit={handleCreate} className="mb-6 space-y-2">
        <input
          aria-label="name"
          className="block w-full border p-2"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder="Name"
          required
        />
        <textarea
          aria-label="description"
          className="block w-full border p-2"
          value={form.description}
          onChange={(e) =>
            setForm({ ...form, description: e.target.value })
          }
          placeholder="Description"
          required
        />
        <button type="submit" className="px-4 py-2 text-white bg-blue-600">
          Add Recipe
        </button>
      </form>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {recipes.map((recipe) => (
          <Link
            to={`/recipes/${recipe.id}`}
            key={recipe.id}
            className="block p-6 bg-white rounded-lg shadow-md"
          >
            <h3 className="text-xl font-bold">{recipe.name}</h3>
            <p className="mt-2 text-gray-600">{recipe.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
