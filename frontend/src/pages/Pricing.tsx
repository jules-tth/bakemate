import { FormEvent, useEffect, useState } from 'react';
import { getPricingConfig, savePricingConfig } from '../api/pricing';

export default function Pricing() {
  const [form, setForm] = useState({
    hourly_rate: '',
    overhead_per_month: ''
  });

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await getPricingConfig();
        setForm({
          hourly_rate: data.hourly_rate.toString(),
          overhead_per_month: data.overhead_per_month.toString()
        });
      } catch (error) {
        console.error(error);
      }
    };
    fetchConfig();
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const updated = await savePricingConfig({
        hourly_rate: Number(form.hourly_rate),
        overhead_per_month: Number(form.overhead_per_month)
      });
      setForm({
        hourly_rate: updated.hourly_rate.toString(),
        overhead_per_month: updated.overhead_per_month.toString()
      });
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Pricing Configuration</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="hourly_rate" className="block">
            Hourly Rate
          </label>
          <input
            id="hourly_rate"
            aria-label="hourly_rate"
            className="border p-2"
            type="number"
            step="0.01"
            value={form.hourly_rate}
            onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })}
            required
          />
        </div>
        <div>
          <label htmlFor="overhead_per_month" className="block">
            Overhead Per Month
          </label>
          <input
            id="overhead_per_month"
            aria-label="overhead_per_month"
            className="border p-2"
            type="number"
            step="0.01"
            value={form.overhead_per_month}
            onChange={(e) =>
              setForm({ ...form, overhead_per_month: e.target.value })
            }
            required
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 text-white bg-blue-600"
        >
          Save
        </button>
      </form>
    </div>
  );
}
