
import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';

export default function ExpensesList() {
  const [expenses, setExpenses] = useState([]);

  useEffect(() => {
    fetch('/api/expenses')
      .then(res => res.json())
      .then(setExpenses)
      .catch(console.error);
  }, []);

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-xl font-semibold mb-4">My Expenses</h1>
      {expenses.map(exp => (
        <Card key={exp.id} className="mb-3">
          <CardContent className="p-4">
            <p className="font-medium">${exp.amount} - {exp.category}</p>
            <p className="text-sm">{exp.description}</p>
            <p className="text-xs text-muted">Submitted on {exp.date}</p>
            <p className={`text-xs font-semibold ${exp.status === 'Approved' ? 'text-green-600' : exp.status === 'Rejected' ? 'text-red-500' : 'text-yellow-600'}`}>
              Status: {exp.status}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
