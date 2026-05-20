/* ===== Calculator Section ===== */

const Calc = {
  current: '0',
  prev: '',
  operator: null,
  waitingForNext: false,
  history: [],

  init() {
    document.querySelectorAll('.calc-btn[data-num]').forEach(btn => {
      btn.addEventListener('click', () => this.inputNum(btn.dataset.num));
    });
    document.querySelectorAll('.calc-btn[data-op]').forEach(btn => {
      btn.addEventListener('click', () => this.inputOp(btn.dataset.op));
    });
    document.querySelectorAll('.calc-btn[data-action]').forEach(btn => {
      btn.addEventListener('click', () => this.doAction(btn.dataset.action));
    });

    document.addEventListener('keydown', e => this.handleKey(e));

    // Add conveyor label
    const conveyor = document.getElementById('calcConveyor');
    const label = document.createElement('div');
    label.className = 'conveyor-label';
    label.textContent = 'История';
    conveyor.insertBefore(label, conveyor.firstChild);

    this.updateDisplay();
  },

  inputNum(num) {
    if (this.waitingForNext) {
      this.current = num;
      this.waitingForNext = false;
    } else {
      this.current = this.current === '0' ? num : this.current + num;
    }
    this.updateDisplay();
  },

  inputOp(op) {
    const val = parseFloat(this.current);
    if (this.operator && !this.waitingForNext) {
      const result = this.calculate(parseFloat(this.prev), val, this.operator);
      this.addHistory(`${this.prev} ${this.opSymbol(this.operator)} ${this.current} = ${result}`);
      this.current = String(result);
      this.prev = String(result);
    } else {
      this.prev = this.current;
    }
    this.operator = op;
    this.waitingForNext = true;
    this.updateDisplay();
  },

  doAction(action) {
    if (action === 'clear') {
      this.current = '0'; this.prev = ''; this.operator = null; this.waitingForNext = false;
    } else if (action === 'sign') {
      this.current = String(-parseFloat(this.current));
    } else if (action === 'percent') {
      this.current = String(parseFloat(this.current) / 100);
    } else if (action === 'decimal') {
      if (!this.current.includes('.')) this.current += '.';
    } else if (action === 'equals') {
      if (!this.operator) return;
      const val = parseFloat(this.current);
      const result = this.calculate(parseFloat(this.prev), val, this.operator);
      this.addHistory(`${this.prev} ${this.opSymbol(this.operator)} ${this.current} = ${result}`);
      this.current = String(result);
      this.prev = '';
      this.operator = null;
      this.waitingForNext = true;
    }
    this.updateDisplay();
  },

  calculate(a, b, op) {
    switch (op) {
      case '+': return this.round(a + b);
      case '-': return this.round(a - b);
      case '*': return this.round(a * b);
      case '/': return b === 0 ? 'Ошибка' : this.round(a / b);
    }
  },

  round(n) {
    return Math.round(n * 1e10) / 1e10;
  },

  opSymbol(op) {
    return { '+': '+', '-': '−', '*': '×', '/': '÷' }[op] || op;
  },

  updateDisplay() {
    document.getElementById('calcResult').textContent = this.formatNum(this.current);
    const expr = this.prev && this.operator ? `${this.prev} ${this.opSymbol(this.operator)}` : '';
    document.getElementById('calcExpression').textContent = expr;
  },

  formatNum(n) {
    const str = String(n);
    if (str.length > 12) return parseFloat(n).toExponential(4);
    return str;
  },

  addHistory(entry) {
    this.history.unshift(entry);
    if (this.history.length > 20) this.history.pop();

    const conveyor = document.getElementById('calcConveyor');
    const existingItems = conveyor.querySelectorAll('.conveyor-item');
    existingItems.forEach(el => el.remove());

    this.history.slice(0, 15).forEach(h => {
      const el = document.createElement('div');
      el.className = 'conveyor-item';
      el.textContent = h;
      conveyor.appendChild(el);
    });

    // Also add to history panel
    const histEl = document.getElementById('calcHistory');
    const item = document.createElement('div');
    item.className = 'calc-history-item';
    item.textContent = entry;
    histEl.appendChild(item);
    histEl.scrollTop = histEl.scrollHeight;
  },

  handleKey(e) {
    if (document.getElementById('section-calc').classList.contains('hidden')) return;
    if (e.key >= '0' && e.key <= '9') this.inputNum(e.key);
    else if (e.key === '.') this.doAction('decimal');
    else if (e.key === '+') this.inputOp('+');
    else if (e.key === '-') this.inputOp('-');
    else if (e.key === '*') this.inputOp('*');
    else if (e.key === '/') { e.preventDefault(); this.inputOp('/'); }
    else if (e.key === 'Enter' || e.key === '=') this.doAction('equals');
    else if (e.key === 'Escape' || e.key === 'c') this.doAction('clear');
    else if (e.key === 'Backspace') {
      if (this.current.length > 1) this.current = this.current.slice(0, -1);
      else this.current = '0';
      this.updateDisplay();
    }
  }
};
