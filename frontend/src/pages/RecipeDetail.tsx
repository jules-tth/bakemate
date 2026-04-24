import { FormEvent, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getRecipe, updateRecipe, deleteRecipe } from '../api/recipes';
import type { Recipe } from '../api/recipes';

export default function RecipeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [form, setForm] = useState({ name: '', description: '' });

  useEffect(() => {
    if (!id) return;
    const fetchRecipe = async () => {
      try {
        const data = await getRecipe(id);
        setRecipe(data);
        setForm({ name: data.name, description: data.description });
      } catch (error) {
        console.error(error);
      }
    };
    fetchRecipe();
  }, [id]);

  const handleUpdate = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      const updated = await updateRecipe(id, form);
      setRecipe(updated);
    } catch (error) {
      console.error(error);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await deleteRecipe(id);
      navigate('/recipes');
    } catch (error) {
      console.error(error);
    }
  };

  if (!recipe) return <div>Loading...</div>;

  return (
    <div>
      <h2 className="mb-4 text-2xl font-bold">Edit Recipe</h2>
      <form onSubmit={handleUpdate} className="space-y-4">
        <input
          aria-label="name"
          className="block w-full border p-2"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <textarea
          aria-label="description"
          className="block w-full border p-2"
          value={form.description}
          onChange={(e) =>
            setForm({ ...form, description: e.target.value })
          }
          required
        />
        <div className="space-x-2">
          <button type="submit" className="px-4 py-2 text-white bg-green-600">
            Save
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className="px-4 py-2 text-white bg-red-600"
          >
            Delete
          </button>
        </div>
      </form>
    </div>
  );
}
