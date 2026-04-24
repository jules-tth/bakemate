import { FormEvent, useEffect, useState } from 'react';
import { listIngredients, createIngredient, updateIngredient } from '../api/ingredients';
import type { Ingredient } from '../api/ingredients';

export default function Ingredients() {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [form, setForm] = useState({ name: '', unit: '', cost: '' });
  const [editing, setEditing] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: '', unit: '', cost: '' });

  useEffect(() => {
    const fetchIngredients = async () => {
      try {
        const data = await listIngredients();
        setIngredients(data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchIngredients();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const newIngredient = await createIngredient({
        name: form.name,
        unit: form.unit,
        cost: Number(form.cost),
      });
      setIngredients((prev) => [...prev, newIngredient]);
      setForm({ name: '', unit: '', cost: '' });
    } catch (error) {
      console.error(error);
    }
  };

  const startEdit = (ing: Ingredient) => {
    setEditing(ing.id);
    setEditForm({
      name: ing.name,
      unit: ing.unit,
      cost: ing.cost.toString(),
    });
  };

  const handleEdit = async (e: FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    try {
      const updated = await updateIngredient(editing, {
        name: editForm.name,
        unit: editForm.unit,
        cost: Number(editForm.cost),
      });
      setIngredients((prev) =>
        prev.map((ing) => (ing.id === updated.id ? updated : ing))
      );
      setEditing(null);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Ingredients</h1>

      <form onSubmit={handleCreate} className="mb-6 space-x-2">
        <input
          aria-label="name"
          className="border p-2"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder="Name"
          required
        />
        <input
          aria-label="unit"
          className="border p-2"
          value={form.unit}
          onChange={(e) => setForm({ ...form, unit: e.target.value })}
          placeholder="Unit"
          required
        />
        <input
          aria-label="cost"
          className="border p-2"
          type="number"
          step="0.01"
          value={form.cost}
          onChange={(e) => setForm({ ...form, cost: e.target.value })}
          placeholder="Cost"
          required
        />
        <button type="submit" className="px-4 py-2 text-white bg-blue-600">
          Add
        </button>
      </form>

      <ul className="space-y-4">
        {ingredients.map((ing) => (
          <li key={ing.id} className="p-4 bg-white rounded shadow">
            {editing === ing.id ? (
              <form onSubmit={handleEdit} className="space-x-2">
                <input
                  aria-label="edit-name"
                  className="border p-2"
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                  required
                />
                <input
                  aria-label="edit-unit"
                  className="border p-2"
                  value={editForm.unit}
                  onChange={(e) =>
                    setEditForm({ ...editForm, unit: e.target.value })
                  }
                  required
                />
                <input
                  aria-label="edit-cost"
                  className="border p-2"
                  type="number"
                  step="0.01"
                  value={editForm.cost}
                  onChange={(e) =>
                    setEditForm({ ...editForm, cost: e.target.value })
                  }
                  required
                />
                <button
                  type="submit"
                  className="px-3 py-1 text-white bg-green-600"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setEditing(null)}
                  className="px-3 py-1 text-white bg-gray-500"
                >
                  Cancel
                </button>
              </form>
            ) : (
              <div className="flex items-center justify-between">
                <span>
                  {ing.name} - {ing.unit} (${ing.cost})
                </span>
                <button
                  type="button"
                  className="px-3 py-1 text-white bg-blue-600"
                  onClick={() => startEdit(ing)}
                >
                  Edit
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
