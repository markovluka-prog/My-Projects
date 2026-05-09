/* ===== Habits Section ===== */

const Habits = {
  data: [],
  plants: ['🌱','🌿','🌾','🌻','🌺','🌹','🌸','🌼'],
  plantWilting: ['🥀','🍂'],

  init() {
    this.data = Storage.get('habits', []);
    document.getElementById('addHabitBtn').addEventListener('click', () => this.addHabit());
    this.checkDailyReset();
    this.render();
  },

  checkDailyReset() {
    const today = new Date().toDateString();
    const lastCheck = Storage.get('habitsLastCheck', '');
    if (lastCheck !== today) {
      Storage.set('habitsLastCheck', today);
    }
  },

  addHabit() {
    const name = prompt('Название привычки:');
    if (!name) return;
    const freq = prompt('Как часто? (ежедневно / по будням / еженедельно)', 'ежедневно') || 'ежедневно';
    const habit = {
      id: Date.now(),
      name: name.trim(),
      freq,
      streak: 0,
      doneToday: false,
      missedDays: 0,
      plantIdx: 0
    };
    this.data.push(habit);
    this.save();
    this.render();
  },

  markDone(habit) {
    if (habit.doneToday) return;
    habit.doneToday = true;
    habit.streak++;
    habit.missedDays = 0;
    if (habit.streak % 3 === 0 && habit.plantIdx < this.plants.length - 1) {
      habit.plantIdx++;
    }
    this.save();
    this.render();
  },

  deleteHabit(id) {
    this.data = this.data.filter(h => h.id !== id);
    this.save();
    this.render();
  },

  getPlantEmoji(habit) {
    if (habit.missedDays >= 3) return this.plantWilting[1];
    if (habit.missedDays >= 1) return this.plantWilting[0];
    return this.plants[Math.min(habit.plantIdx, this.plants.length - 1)];
  },

  render() {
    const container = document.getElementById('gardenBeds');
    container.innerHTML = '';
    this.data.forEach(habit => {
      const bed = document.createElement('div');
      bed.className = 'habit-bed';

      const plantClass = habit.missedDays >= 3 ? 'dried' : habit.missedDays >= 1 ? 'wilting' : '';

      bed.innerHTML = `
        <button class="habit-bed__delete" title="Удалить">✕</button>
        <div class="habit-bed__plant ${plantClass}">${this.getPlantEmoji(habit)}</div>
        <div class="habit-bed__name">${habit.name}</div>
        <div class="habit-bed__streak">🔥 ${habit.streak} дней подряд</div>
        <div class="habit-bed__freq">📅 ${habit.freq}</div>
        <div class="habit-bed__check ${habit.doneToday ? 'done' : ''}">${habit.doneToday ? '✓' : '○'}</div>
        <div class="habit-soil"></div>
      `;

      bed.querySelector('.habit-bed__check').addEventListener('click', () => this.markDone(habit));
      bed.querySelector('.habit-bed__delete').addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm(`Удалить привычку «${habit.name}»?`)) this.deleteHabit(habit.id);
      });

      container.appendChild(bed);
    });

    if (!this.data.length) {
      const empty = document.createElement('p');
      empty.style.cssText = 'color:var(--habit-dark);opacity:0.5;font-style:italic;';
      empty.textContent = 'Посадите первую привычку нажав кнопку ниже 🌱';
      container.appendChild(empty);
    }
  },

  save() {
    Storage.set('habits', this.data);
  }
};
