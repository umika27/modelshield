/**
 * DataTable Component
 * Renders dense developer data grid with sticky headers and monospace cells.
 */
export function createDataTable({ headers, rows, id = "" }) {
  if (!rows || rows.length === 0) {
    return `<div class="empty-state">No records available in current view.</div>`;
  }

  const thHtml = headers.map(h => `<th>${h}</th>`).join("");
  const trHtml = rows.map(r => {
    const tdHtml = r.map(cell => `<td>${cell}</td>`).join("");
    return `<tr>${tdHtml}</tr>`;
  }).join("");

  return `
    <div class="table-container" ${id ? `id="${id}"` : ""}>
      <table class="dev-table">
        <thead><tr>${thHtml}</tr></thead>
        <tbody>${trHtml}</tbody>
      </table>
    </div>
  `;
}
