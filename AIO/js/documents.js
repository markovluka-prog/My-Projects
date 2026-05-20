/* ===== Documents Section ===== */

const Documents = {
  data: { inbox: [], signed: [] },

  init() {
    this.data = Storage.get('documents', { inbox: [], signed: [] });

    document.getElementById('scanDocBtn').addEventListener('click', () => {
      document.getElementById('docFileInput').click();
    });

    document.getElementById('docFileInput').addEventListener('change', e => {
      const file = e.target.files[0];
      if (!file) return;
      const doc = {
        id: Date.now(),
        name: file.name,
        date: new Date().toLocaleDateString('ru-RU'),
        type: file.type
      };
      this.data.inbox.push(doc);
      this.save();
      this.render();
      e.target.value = '';
    });

    this.render();
  },

  sign(docId) {
    const doc = this.data.inbox.find(d => d.id === docId);
    if (!doc) return;
    this.data.inbox = this.data.inbox.filter(d => d.id !== docId);
    this.data.signed.push({ ...doc, signedDate: new Date().toLocaleDateString('ru-RU') });
    this.save();
    this.render();
  },

  render() {
    const lettersEl = document.getElementById('mailboxLetters');
    lettersEl.innerHTML = '';

    if (!this.data.inbox.length) {
      lettersEl.innerHTML = '<p style="color:#aaa;font-style:italic;font-size:0.85rem;">Нет документов. Отсканируйте первый!</p>';
    } else {
      this.data.inbox.forEach(doc => {
        const el = document.createElement('div');
        el.className = 'letter-card';
        el.innerHTML = `
          <div class="letter-card__icon">📄</div>
          <div class="letter-card__info">
            <div class="letter-card__name">${doc.name}</div>
            <div class="letter-card__date">${doc.date}</div>
          </div>
          <button class="letter-card__sign-btn">🔏 Подписать</button>
        `;
        el.querySelector('.letter-card__sign-btn').addEventListener('click', (e) => {
          e.stopPropagation();
          this.sign(doc.id);
        });
        lettersEl.appendChild(el);
      });
    }

    const signedEl = document.getElementById('mailboxSigned');
    signedEl.innerHTML = '';
    this.data.signed.forEach(doc => {
      const el = document.createElement('div');
      el.className = 'signed-card';
      el.innerHTML = `
        <span class="signed-card__seal">🔏</span>
        <span class="signed-card__name">${doc.name}</span>
        <span style="font-size:0.68rem;color:#aaa;">${doc.signedDate}</span>
      `;
      signedEl.appendChild(el);
    });
  },

  save() {
    Storage.set('documents', this.data);
  }
};
