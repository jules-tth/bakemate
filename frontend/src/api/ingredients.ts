import apiClient from './index';

export interface Ingredient {
  id: string;
  name: string;
  unit: string;
  cost: number;
  description?: string;
}

export type IngredientInput = Omit<Ingredient, 'id'>;

export async function listIngredients(): Promise<Ingredient[]> {
  const response = await apiClient.get<Ingredient[]>('/ingredients');
  return response.data;
}

export async function createIngredient(ingredient: IngredientInput): Promise<Ingredient> {
  const response = await apiClient.post<Ingredient>('/ingredients', ingredient);
  return response.data;
}

export async function updateIngredient(id: string, ingredient: Partial<IngredientInput>): Promise<Ingredient> {
  const response = await apiClient.put<Ingredient>(`/ingredients/${id}`, ingredient);
  return response.data;
}

export async function deleteIngredient(id: string): Promise<void> {
  await apiClient.delete(`/ingredients/${id}`);
}

