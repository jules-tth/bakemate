import { useEffect, useState, FormEvent } from 'react';
import { listCalendarEvents, createCalendarEvent } from '../api/calendar';
import type { CalendarEvent } from '../api/calendar';
import { listTasks, createTask } from '../api/tasks';
import type { Task } from '../api/tasks';

export default function Calendar() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskTitle, setTaskTitle] = useState('');
  const [eventTitle, setEventTitle] = useState('');
  const [eventDate, setEventDate] = useState('');

  useEffect(() => {
    async function load() {
      setEvents(await listCalendarEvents());
      setTasks(await listTasks());
    }
    load();
  }, []);

  async function handleTaskSubmit(e: FormEvent) {
    e.preventDefault();
    const newTask = await createTask({ title: taskTitle, status: 'pending' });
    setTasks([...tasks, newTask]);
    setTaskTitle('');
  }

  async function handleEventSubmit(e: FormEvent) {
    e.preventDefault();
    const date = eventDate || new Date().toISOString();
    const newEvent = await createCalendarEvent({
      title: eventTitle,
      start_datetime: date,
      end_datetime: date,
    });
    setEvents([...events, newEvent]);
    setEventTitle('');
    setEventDate('');
  }

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold mb-2">Tasks</h2>
        <form onSubmit={handleTaskSubmit} className="space-x-2">
          <label htmlFor="taskTitle">Task Title</label>
          <input
            id="taskTitle"
            value={taskTitle}
            onChange={(e) => setTaskTitle(e.target.value)}
            className="border p-1"
          />
          <button type="submit" className="bg-blue-500 text-white px-2 py-1">Add Task</button>
        </form>
        <ul className="mt-4 list-disc pl-5">
          {tasks.map((t) => (
            <li key={t.id}>{t.title}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Calendar Events</h2>
        <form onSubmit={handleEventSubmit} className="space-x-2">
          <label htmlFor="eventTitle">Event Title</label>
          <input
            id="eventTitle"
            value={eventTitle}
            onChange={(e) => setEventTitle(e.target.value)}
            className="border p-1"
          />
          <label htmlFor="eventDate">Event Date</label>
          <input
            id="eventDate"
            type="date"
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
            className="border p-1"
          />
          <button type="submit" className="bg-blue-500 text-white px-2 py-1">Add Event</button>
        </form>
        <ul className="mt-4 list-disc pl-5">
          {events.map((e) => (
            <li key={e.id}>{e.title}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
