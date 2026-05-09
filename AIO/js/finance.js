/* ===== Finance Section ===== */

const Finance = {
  data: { income: [], expenses: [] },
  categories: [
    { name: 'Еда', icon: '🍕' },
    { name: 'Транспорт', icon: '🚗' },
    { name: 'Развлечения', icon: '🎉' },
    { name: 'Здоровье', icon: '💊' },
    { name: 'Одежда', icon: '👕' },
    { name: 'Прочее', icon: '📦' },
  ],

  init() {
    this.data = Storage.get('finance', { income: [], expenses: [] });

    document.getElementById('financeAddBtn').addEventListener('click', () => {
      document.getElementById('financeModal').classList.remove('hidden');
    });
    document.getElementById('financeModalCancel').addEventListener('click', () => {
      document.getElementById('financeModal').classList.add('hidden');
    });
    document.getElementById('financeModalSave').addEventListener('click', () => this.saveExpense());

    this.render();
  },

  saveExpense() {
    const amount = parseFloat(document.getElementById('financeAmount').value);
    const category = document.getElementById('financeCategory').value;
    const note = document.getElementById('financeNote').value.trim();
    if (!amount || amount <= 0) return;

    this.data.expenses.push({ amount, category, note, date: new Date().toLocaleDateString('ru-RU') });
    Storage.set('finance', this.data);

    document.getElementById('financeAmount').value = '';
    document.getElementById('financeNote').value = '';
    document.getElementById('financeModal').classList.add('hidden');
    this.render();
  },

  render() {
    const totalExpense = this.data.expenses.reduce((s, e) => s + e.amount, 0);
    const totalIncome = this.data.income.reduce((s, i) => s + i.amount, 0);

    document.getElementById('expenseTotal').textContent = `${totalExpense.toLocaleString('ru-RU')} ₽`;
    document.getElementById('incomeTotal').textContent = `${totalIncome.toLocaleString('ru-RU')} ₽`;

    // Animate scales
    const maxAmount = Math.max(totalIncome, totalExpense, 1);
    const incomeH = 60 + (totalIncome / maxAmount) * 60;
    const expenseH = 60 + (totalExpense / maxAmount) * 60;
    document.getElementById('incomePan').style.minHeight = `${incomeH}px`;
    document.getElementById('expensePan').style.minHeight = `${expenseH}px`;

    // Render cells
    const cellsEl = document.getElementById('financeCells');
    cellsEl.innerHTML = '';
    this.categories.forEach(cat => {
      const catExpenses = this.data.expenses.filter(e => e.category === cat.name);
      const total = catExpenses.reduce((s, e) => s + e.amount, 0);

      const cell = document.createElement('div');
      cell.className = 'finance-cell';
      cell.innerHTML = `
        <div class="finance-cell__icon">${cat.icon}</div>
        <div class="finance-cell__name">${cat.name}</div>
        <div class="finance-cell__amount">${total.toLocaleString('ru-RU')} ₽</div>
        <div class="finance-cell__lock">🔒 ${catExpenses.length} трат</div>
      `;
      cell.addEventListener('click', () => {
        if (!catExpenses.length) { alert(`В категории «${cat.name}» пока нет трат.`); return; }
        const list = catExpenses.map(e => `• ${e.date}: ${e.amount} ₽ — ${e.note || '(без заметки)'}`).join('\n');
        alert(`${cat.icon} ${cat.name}\n\n${list}\n\nИтого: ${total} ₽`);
      });
      cellsEl.appendChild(cell);
    });
  }
};
