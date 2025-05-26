
import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function NewExpense() {
  const [formData, setFormData] = useState({ amount: '', category: '', description: '', receipt: null });

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (name === 'receipt') {
      setFormData({ ...formData, receipt: files[0] });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = new FormData();
    Object.keys(formData).forEach(key => data.append(key, formData[key]));

    fetch('/api/expenses', { method: 'POST', body: data })
      .then(res => res.json())
      .then(response => console.log('Expense submitted:', response))
      .catch(err => console.error('Error submitting expense:', err));
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-xl font-semibold mb-4">New Expense Submission</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Card><CardContent className="p-4 space-y-2">
          <input type="number" name="amount" placeholder="Amount" className="w-full border p-2" onChange={handleChange} required />
          <select name="category" className="w-full border p-2" onChange={handleChange} required>
            <option value="">Select Category</option>
            <option value="Food">Food</option>
            <option value="Travel">Travel</option>
            <option value="Lodging">Lodging</option>
            <option value="Entertainment">Entertainment</option>
          </select>
          <input type="text" name="description" placeholder="Description" className="w-full border p-2" onChange={handleChange} required />
          <input type="file" name="receipt" className="w-full border p-2" onChange={handleChange} required />
          <Button type="submit" className="w-full">Submit Expense</Button>
        </CardContent></Card>
      </form>
    </div>
  );
}
