
import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ExpenseReview() {
  const [pending, setPending] = useState([]);

  useEffect(() => {
    fetch('/api/expenses/pending')
      .then(res => res.json())
      .then(setPending)
      .catch(console.error);
  }, []);

  const handleAction = (id, action) => {
    fetch(`/api/expenses/${id}/${action}`, { method: 'POST' })
      .then(() => setPending(prev => prev.filter(e => e.id !== id)));
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-xl font-semibold mb-4">Review Expenses</h1>
      {pending.map(exp => (
        <Card key={exp.id} className="mb-3">
          <CardContent className="p-4">
            <p className="font-medium">${exp.amount} - {exp.category}</p>
            <p className="text-sm">{exp.description}</p>
            <p className="text-xs text-muted">By {exp.submittedBy} on {exp.date}</p>
            <div className="flex gap-2 mt-2">
              <Button onClick={() => handleAction(exp.id, 'approve')}>Approve</Button>
              <Button onClick={() => handleAction(exp.id, 'reject')} variant="destructive">Reject</Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
