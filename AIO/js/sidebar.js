/* ===== Sidebar ===== */

const Sidebar = {
  isOpen: true,

  init() {
    const toggle = document.getElementById('sidebarToggle');
    const openBtn = document.getElementById('sidebarOpenBtn');
    const overlay = document.getElementById('sidebarOverlay');

    toggle.addEventListener('click', () => this.toggle());
    openBtn.addEventListener('click', () => this.open());
    overlay.addEventListener('click', () => this.close());

    this.initUserPanel();

    // Mobile: start closed
    if (window.innerWidth <= 768) this.close();
  },

  toggle() {
    this.isOpen ? this.close() : this.open();
  },

  open() {
    this.isOpen = true;
    document.getElementById('sidebar').classList.add('sidebar--open');
    document.getElementById('sidebarOpenBtn').classList.add('hidden');
    document.getElementById('mainContent').classList.remove('sidebar-collapsed');
    if (window.innerWidth <= 768) {
      document.getElementById('sidebarOverlay').classList.remove('hidden');
    }
  },

  close() {
    this.isOpen = false;
    document.getElementById('sidebar').classList.remove('sidebar--open');
    document.getElementById('sidebarOpenBtn').classList.remove('hidden');
    document.getElementById('mainContent').classList.add('sidebar-collapsed');
    document.getElementById('sidebarOverlay').classList.add('hidden');
  },

  initUserPanel() {
    const editBtn = document.getElementById('editUserBtn');
    const form = document.getElementById('userForm');
    const saveBtn = document.getElementById('saveUserBtn');
    const inputName = document.getElementById('inputName');
    const inputAge = document.getElementById('inputAge');
    const inputEmoji = document.getElementById('inputEmoji');

    // Load saved user data
    const user = Storage.get('user', { name: 'Гость', age: null, emoji: '👤' });
    inputName.value = user.name !== 'Гость' ? user.name : '';
    inputAge.value = user.age || '';
    inputEmoji.value = user.emoji;

    editBtn.addEventListener('click', () => {
      form.classList.toggle('hidden');
    });

    saveBtn.addEventListener('click', () => {
      const name = inputName.value.trim() || 'Гость';
      const age = parseInt(inputAge.value) || null;
      const emoji = inputEmoji.value;

      const userData = { name, age, emoji };
      Storage.set('user', userData);

      document.getElementById('userName').textContent = name;
      document.getElementById('userAvatar').textContent = emoji;
      document.getElementById('userAgeLabel').textContent = age ? `${age} лет` : 'Укажите возраст';

      form.classList.add('hidden');
    });
  }
};

document.addEventListener('DOMContentLoaded', () => Sidebar.init());
