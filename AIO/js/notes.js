/* ===== Notes Section ===== */

const Notes = {
  data: { shelves: [] },
  selectMode: false,
  selected: new Set(),
  editingBook: null,

  init() {
    this.data = Storage.get('notes', {
      shelves: [
        { id: 1, name: 'Мои записи', books: [] }
      ]
    });

    document.getElementById('addShelfBtn').addEventListener('click', () => this.addShelf());
    document.getElementById('addBookBtn').addEventListener('click', () => this.openNoteTypePicker());
    document.getElementById('notesSelectBtn').addEventListener('click', () => this.toggleSelectMode());
    document.getElementById('cancelSelectBtn').addEventListener('click', () => this.exitSelectMode());
    document.getElementById('deleteSelectedBtn').addEventListener('click', () => this.deleteSelected());
    document.getElementById('printSelectedBtn').addEventListener('click', () => this.printSelected());
    document.getElementById('exportSelectedBtn').addEventListener('click', () => this.exportSelected());
    document.getElementById('noteEditorClose').addEventListener('click', () => this.closeEditor());
    document.getElementById('noteSaveBtn').addEventListener('click', () => this.saveBook());

    document.querySelectorAll('.modal-option[data-note-type]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.createBook(btn.dataset.noteType);
        document.getElementById('noteTypeModal').classList.add('hidden');
      });
    });
    document.getElementById('noteTypeModalClose').addEventListener('click', () => {
      document.getElementById('noteTypeModal').classList.add('hidden');
    });

    this.render();
  },

  render() {
    const container = document.getElementById('shelvesContainer');
    container.innerHTML = '';
    this.data.shelves.forEach(shelf => container.appendChild(this.renderShelf(shelf)));
  },

  renderShelf(shelf) {
    const el = document.createElement('div');
    el.className = 'shelf';
    el.dataset.shelfId = shelf.id;

    const nameEl = document.createElement('div');
    nameEl.className = 'shelf__name';
    nameEl.textContent = shelf.name;
    nameEl.setAttribute('contenteditable', 'true');
    nameEl.addEventListener('blur', () => {
      shelf.name = nameEl.textContent.trim() || 'Полка';
      this.save();
    });

    const booksEl = document.createElement('div');
    booksEl.className = 'shelf__books';

    shelf.books.forEach(book => booksEl.appendChild(this.renderBook(book, shelf)));

    el.appendChild(nameEl);
    el.appendChild(booksEl);
    return el;
  },

  renderBook(book, shelf) {
    const colors = { list: '#2e7d32', form: '#1565c0', note: '#6a1b9a' };
    const icons = { list: '🧾', form: '✅', note: '📝' };

    const el = document.createElement('div');
    el.className = `book book--${book.type}`;
    el.dataset.bookId = book.id;

    const titleEl = document.createElement('span');
    titleEl.className = 'book__title';
    titleEl.textContent = book.title || 'Без названия';

    const iconEl = document.createElement('span');
    iconEl.className = 'book__type-icon';
    iconEl.textContent = icons[book.type] || '📝';

    el.appendChild(titleEl);
    el.appendChild(iconEl);

    el.addEventListener('click', () => {
      if (this.selectMode) {
        this.toggleBookSelection(book.id, el);
      } else {
        this.openEditor(book, shelf);
      }
    });

    if (this.selected.has(book.id)) el.classList.add('selected');

    return el;
  },

  openNoteTypePicker() {
    document.getElementById('noteTypeModal').classList.remove('hidden');
  },

  createBook(type) {
    const shelf = this.data.shelves[0];
    const book = {
      id: Date.now(),
      type,
      title: '',
      subtitle: '',
      content: type === 'list' ? [] : type === 'form' ? [] : ''
    };
    shelf.books.push(book);
    this.save();
    this.render();
    this.openEditor(book, shelf);
  },

  openEditor(book, shelf) {
    this.editingBook = { book, shelf };
    document.getElementById('noteTitle').value = book.title;
    document.getElementById('noteSubtitle').value = book.subtitle || '';
    this.renderEditorBody(book);
    document.getElementById('noteEditor').classList.remove('hidden');
  },

  renderEditorBody(book) {
    const body = document.getElementById('noteBody');
    body.innerHTML = '';

    if (book.type === 'list') {
      book.content.forEach((item, i) => body.appendChild(this.renderListItem(item, i, book)));
      const addBtn = document.createElement('button');
      addBtn.textContent = '+ Пункт';
      addBtn.style.cssText = 'margin-top:8px;padding:5px 12px;background:var(--notes-green);color:#fff;border-radius:6px;font-size:0.82rem;';
      addBtn.addEventListener('click', () => {
        book.content.push({ text: '', checked: false });
        this.renderEditorBody(book);
      });
      body.appendChild(addBtn);

    } else if (book.type === 'note') {
      const area = document.createElement('textarea');
      area.className = 'note-plain-area';
      area.placeholder = 'Пишите здесь...';
      area.value = book.content;
      area.addEventListener('input', () => { book.content = area.value; });
      body.appendChild(area);

    } else if (book.type === 'form') {
      book.content.forEach((q, i) => body.appendChild(this.renderFormQuestion(q, i, book)));
      const addBtn = document.createElement('button');
      addBtn.textContent = '+ Вопрос';
      addBtn.style.cssText = 'margin-top:8px;padding:5px 12px;background:var(--timer-blue);color:#fff;border-radius:6px;font-size:0.82rem;';
      addBtn.addEventListener('click', () => {
        book.content.push({ text: '', type: 'text', answer: '' });
        this.renderEditorBody(book);
      });
      body.appendChild(addBtn);
    }
  },

  renderListItem(item, idx, book) {
    const row = document.createElement('div');
    row.className = 'note-list-item';

    const checkbox = document.createElement('div');
    checkbox.className = 'note-list-checkbox';
    checkbox.textContent = item.checked ? '✓' : '';
    checkbox.style.background = item.checked ? 'var(--notes-green)' : '';
    checkbox.style.color = '#fff';
    checkbox.addEventListener('click', () => {
      item.checked = !item.checked;
      checkbox.textContent = item.checked ? '✓' : '';
      checkbox.style.background = item.checked ? 'var(--notes-green)' : '';
    });

    const input = document.createElement('input');
    input.className = 'note-list-input';
    input.value = item.text;
    input.placeholder = 'Пункт списка...';
    input.addEventListener('input', () => { item.text = input.value; });
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        book.content.splice(idx + 1, 0, { text: '', checked: false });
        this.renderEditorBody(book);
      }
    });

    row.appendChild(checkbox);
    row.appendChild(input);
    return row;
  },

  renderFormQuestion(q, idx, book) {
    const row = document.createElement('div');
    row.style.cssText = 'display:flex;gap:8px;align-items:center;padding:6px 0;border-bottom:1px dashed rgba(0,0,0,0.08);';

    const input = document.createElement('input');
    input.style.cssText = 'flex:1;font-family:Caveat,cursive;font-size:1rem;background:transparent;border-bottom:1px solid rgba(0,0,0,0.2);padding:2px;';
    input.value = q.text;
    input.placeholder = 'Вопрос...';
    input.addEventListener('input', () => { q.text = input.value; });

    const del = document.createElement('button');
    del.textContent = '✕';
    del.style.cssText = 'color:#aaa;font-size:0.9rem;';
    del.addEventListener('click', () => {
      book.content.splice(idx, 1);
      this.renderEditorBody(book);
    });

    row.appendChild(input);
    row.appendChild(del);
    return row;
  },

  closeEditor() {
    document.getElementById('noteEditor').classList.add('hidden');
    this.editingBook = null;
  },

  saveBook() {
    if (!this.editingBook) return;
    const { book } = this.editingBook;
    book.title = document.getElementById('noteTitle').value.trim() || 'Без названия';
    book.subtitle = document.getElementById('noteSubtitle').value.trim();
    this.save();
    this.render();
    this.closeEditor();
  },

  toggleSelectMode() {
    this.selectMode = !this.selectMode;
    const bar = document.getElementById('notesSelectBar');
    const btn = document.getElementById('notesSelectBtn');
    bar.classList.toggle('hidden', !this.selectMode);
    btn.textContent = this.selectMode ? 'Отмена' : 'Выбрать';
    if (!this.selectMode) {
      this.selected.clear();
      this.render();
    }
  },

  exitSelectMode() {
    this.selectMode = false;
    this.selected.clear();
    document.getElementById('notesSelectBar').classList.add('hidden');
    document.getElementById('notesSelectBtn').textContent = 'Выбрать';
    this.render();
  },

  toggleBookSelection(bookId, el) {
    if (this.selected.has(bookId)) {
      this.selected.delete(bookId);
      el.classList.remove('selected');
    } else {
      this.selected.add(bookId);
      el.classList.add('selected');
    }
    document.getElementById('selectedCount').textContent = `${this.selected.size} выбрано`;
  },

  deleteSelected() {
    if (!this.selected.size) return;
    this.data.shelves.forEach(shelf => {
      shelf.books = shelf.books.filter(b => !this.selected.has(b.id));
    });
    this.save();
    this.exitSelectMode();
  },

  printSelected() {
    if (!this.selected.size) return;
    const books = this.getAllBooks().filter(b => this.selected.has(b.id));
    const content = books.map(b => `<h2>${b.title}</h2><pre>${JSON.stringify(b.content, null, 2)}</pre>`).join('<hr/>');
    const win = window.open('', '_blank');
    win.document.write(`<html><body style="font-family:sans-serif;">${content}</body></html>`);
    win.print();
    this.exitSelectMode();
  },

  exportSelected() {
    const books = this.getAllBooks().filter(b => this.selected.has(b.id) && b.type === 'form');
    if (!books.length) {
      alert('Выберите хотя бы одну Форму для экспорта.');
      return;
    }
    books.forEach(b => {
      const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${b.title}</title></head><body><h1>${b.title}</h1>${b.content.map((q,i) => `<p><b>${i+1}. ${q.text}</b><br/><input type="text" placeholder="Ответ..."/></p>`).join('')}</body></html>`;
      const blob = new Blob([html], { type: 'text/html' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = b.title + '.html';
      a.click();
    });
    this.exitSelectMode();
  },

  addShelf() {
    const name = prompt('Название полки:');
    if (!name) return;
    this.data.shelves.push({ id: Date.now(), name: name.trim(), books: [] });
    this.save();
    this.render();
  },

  getAllBooks() {
    return this.data.shelves.flatMap(s => s.books);
  },

  save() {
    Storage.set('notes', this.data);
  }
};
