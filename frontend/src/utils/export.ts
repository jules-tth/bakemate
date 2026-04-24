import Papa from 'papaparse';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import type { Order } from '../api/orders';

export function exportOrdersCSV(orders: Order[]) {
  const csv = Papa.unparse(orders);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'orders.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function exportOrdersPDF(element: HTMLElement, rangeLabel: string) {
  const canvas = await html2canvas(element);
  const imgData = canvas.toDataURL('image/png');
  const pdf = new jsPDF('p', 'mm', 'a4');
  const width = pdf.internal.pageSize.getWidth();
  const height = (canvas.height * width) / canvas.width;
  pdf.text(`Orders — ${rangeLabel}`, 10, 10);
  pdf.addImage(imgData, 'PNG', 0, 20, width, height);
  pdf.save('orders.pdf');
}

export function exportCSV<T extends object>(data: T[], filename: string) {
  const csv = Papa.unparse(data);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function exportElementPDF(element: HTMLElement, title: string, filename: string) {
  const canvas = await html2canvas(element);
  const imgData = canvas.toDataURL('image/png');
  const pdf = new jsPDF('p', 'mm', 'a4');
  const width = pdf.internal.pageSize.getWidth();
  const height = (canvas.height * width) / canvas.width;
  pdf.text(title, 10, 10);
  pdf.addImage(imgData, 'PNG', 0, 20, width, height);
  pdf.save(filename);
}
