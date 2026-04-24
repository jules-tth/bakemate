import apiClient from './index';

export interface Recipe {
  id: string;
  name: string;
  description: string;
}

export async function listRecipes(): Promise<Recipe[]> {
  const response = await apiClient.get<Recipe[]>('/recipes');
  return response.data;
}

export async function getRecipe(id: string): Promise<Recipe> {
  const response = await apiClient.get<Recipe>(`/recipes/${id}`);
  return response.data;
}

export async function createRecipe(recipe: Omit<Recipe, 'id'>): Promise<Recipe> {
  const response = await apiClient.post<Recipe>('/recipes', recipe);
  return response.data;
}

export async function updateRecipe(id: string, recipe: Partial<Recipe>): Promise<Recipe> {
  const response = await apiClient.put<Recipe>(`/recipes/${id}`, recipe);
  return response.data;
}

export async function deleteRecipe(id: string): Promise<void> {
  await apiClient.delete(`/recipes/${id}`);
}
