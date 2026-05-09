/* ===== Family Section ===== */

const Family = {
  data: { members: [], events: [], shoppingList: [] },

  init() {
    this.data = Storage.get('family', {
      members: [{ id: 1, name: 'Я', icon: '🧑' }],
      events: [],
      shoppingList: []
    });

    document.getElementById('addFamilyMemberBtn').addEventListener('click', () => this.addMember());
    document.getElementById('addFamilyEventBtn').addEventListener('click', () => this.addEvent());
    document.getElementById('addShoppingItemBtn').addEventListener('click', () => this.addShoppingItem());
    document.getElementById('shoppingInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') this.addShoppingItem();
    });

    this.render();
  },

  addMember() {
    const name = prompt('Имя участника:');
    if (!name) return;
    const icons = ['👨','👩','🧒','👴','👵','🧑'];
    const icon = icons[this.data.members.length % icons.length];
    this.data.members.push({ id: Date.now(), name: name.trim(), icon });
    this.save();
    this.render();
  },

  addEvent() {
    const name = prompt('Название события:');
    if (!name) return;
    this.data.events.push({ id: Date.now(), name: name.trim(), date: new Date().toLocaleDateString('ru-RU') });
    this.save();
    this.renderEvents();
  },

  addShoppingItem() {
    const input = document.getElementById('shoppingInput');
    const name = input.value.trim();
    if (!name) return;
    this.data.shoppingList.push({ id: Date.now(), name, checked: false });
    input.value = '';
    this.save();
    this.renderShopping();
  },

  render() {
    this.renderMembers();
    this.renderEvents();
    this.renderShopping();
  },

  renderMembers() {
    const container = document.getElementById('villageHouses');
    container.innerHTML = '';
    this.data.members.forEach(m => {
      const house = document.createElement('div');
      house.className = 'village-house';
      house.innerHTML = `
        <div class="village-house__icon">${m.icon}🏠</div>
        <div class="village-house__name">${m.name}</div>
      `;
      container.appendChild(house);
    });
  },

  renderEvents() {
    const container = document.getElementById('villageEvents');
    container.innerHTML = '';
    this.data.events.slice(-5).forEach(ev => {
      const el = document.createElement('div');
      el.className = 'village-event';
      el.textContent = `${ev.date}: ${ev.name}`;
      container.appendChild(el);
    });
  },

  renderShopping() {
    const container = document.getElementById('villageShoppingList');
    container.innerHTML = '';
    this.data.shoppingList.forEach(item => {
      const el = document.createElement('div');
      el.className = 'shopping-item' + (item.checked ? ' checked' : '');
      el.innerHTML = `
        <span class="shopping-item__check">${item.checked ? '✅' : '☐'}</span>
        <span class="shopping-item__name">${item.name}</span>
        <span class="shopping-item__del">✕</span>
      `;
      el.querySelector('.shopping-item__check').addEventListener('click', () => {
        item.checked = !item.checked;
        this.save();
        this.renderShopping();
      });
      el.querySelector('.shopping-item__del').addEventListener('click', () => {
        this.data.shoppingList = this.data.shoppingList.filter(i => i.id !== item.id);
        this.save();
        this.renderShopping();
      });
      container.appendChild(el);
    });
  },

  save() {
    Storage.set('family', this.data);
  }
};
