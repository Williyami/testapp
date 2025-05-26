
import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ExpensePolicies() {
  const [policies, setPolicies] = useState([]);
  const [form, setForm] = useState({ category: '', limit: '', role: '' });

  useEffect(() => {
    fetch('/api/policies')
      .then(res => res.json())
      .then(setPolicies);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('/api/policies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
      .then(res => res.json())
      .then(data => {
        setPolicies([...policies, data]);
        setForm({ category: '', limit: '', role: '' });
      });
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-xl font-semibold mb-4">Expense Policies</h1>

      <form onSubmit={handleSubmit} className="space-y-2 mb-4">
        <input className="w-full border p-2" placeholder="Category" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} />
        <input className="w-full border p-2" placeholder="Limit Amount" type="number" value={form.limit} onChange={e => setForm({ ...form, limit: e.target.value })} />
        <input className="w-full border p-2" placeholder="Role" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} />
        <Button type="submit" className="w-full">Add Policy</Button>
      </form>

      <div className="space-y-2">
        {policies.map((policy, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <p><strong>{policy.category}</strong> for {policy.role}</p>
              <p className="text-sm">Limit: ${policy.limit}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
