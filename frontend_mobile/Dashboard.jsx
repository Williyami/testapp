
import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Settings, Plane, Utensils } from 'lucide-react';

export default function ExpenseDashboard() {
  const [dashboardData, setDashboardData] = useState({
    totalSpending: 0,
    flaggedExpenses: 0,
    policyViolations: 0,
    monthlySpending: [],
    categorySpending: [],
    flaggedItems: [],
  });

  useEffect(() => {
    fetch('/api/dashboard')
      .then((res) => res.json())
      .then((data) => setDashboardData(data))
      .catch((err) => console.error('Error fetching dashboard data:', err));
  }, []);

  return (
    <div className="p-4 space-y-6 max-w-md mx-auto text-sm">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">Expense Dashboard</h1>
        <Settings className="w-5 h-5" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card><CardContent className="p-4"><p className="text-muted">Total Spending</p><h2 className="text-xl font-bold">${dashboardData.totalSpending}</h2></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-muted">Flagged Expenses</p><h2 className="text-xl font-bold">{dashboardData.flaggedExpenses}</h2></CardContent></Card>
        <Card className="col-span-2"><CardContent className="p-4"><p className="text-muted">Policy Violations</p><h2 className="text-xl font-bold">{dashboardData.policyViolations}</h2></CardContent></Card>
      </div>

      <div className="space-y-4">
        <h2 className="font-semibold">Spending Overview</h2>
        <Card><CardContent className="p-4"><ResponsiveContainer width="100%" height={100}><LineChart data={dashboardData.monthlySpending}><XAxis dataKey="month" /><YAxis /><Tooltip /><Line type="monotone" dataKey="amount" stroke="#4F46E5" strokeWidth={2} /></LineChart></ResponsiveContainer></CardContent></Card>
        <Card><CardContent className="p-4"><ResponsiveContainer width="100%" height={100}><LineChart data={dashboardData.categorySpending}><XAxis dataKey="category" /><YAxis /><Tooltip /><Line type="monotone" dataKey="amount" stroke="#4F46E5" strokeWidth={2} /></LineChart></ResponsiveContainer></CardContent></Card>
      </div>

      <div className="space-y-2">
        <h2 className="font-semibold">Flagged Expenses</h2>
        {dashboardData.flaggedItems.map((item, index) => (
          <Card key={index}><CardContent className="p-4 flex items-start gap-2">
            {item.category === 'Travel' ? <Plane className="w-5 h-5 mt-1" /> : <Utensils className="w-5 h-5 mt-1" />}
            <div><p>${item.amount} - {item.description}</p><p className="text-xs text-muted">Submitted by {item.submittedBy}</p><p className="text-xs">{item.category}</p></div>
          </CardContent></Card>
        ))}
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-white border-t flex justify-around py-2 text-xs">
        <Button variant="ghost">Dashboard</Button>
        <Button variant="ghost">Expenses</Button>
        <Button variant="ghost">Reports</Button>
        <Button variant="ghost">Settings</Button>
      </div>
    </div>
  );
}
