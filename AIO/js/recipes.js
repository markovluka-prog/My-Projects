/* ===== Recipes Section ===== */

const Recipes = {
  selectedIngredients: new Set(),
  savedRecipes: [],

  stalls: [
    {
      name: '🥩 Мясо', items: ['Курица', 'Говядина', 'Свинина', 'Рыба', 'Тунец']
    },
    {
      name: '🥦 Овощи', items: ['Картошка', 'Морковь', 'Лук', 'Помидор', 'Огурец', 'Капуста', 'Перец']
    },
    {
      name: '🥛 Молочное', items: ['Молоко', 'Яйца', 'Сыр', 'Сметана', 'Масло']
    },
    {
      name: '🌾 Крупы', items: ['Рис', 'Гречка', 'Макароны', 'Хлеб', 'Мука']
    },
    {
      name: '🌿 Приправы', items: ['Соль', 'Перец', 'Чеснок', 'Укроп', 'Базилик']
    }
  ],

  recipeDB: [
    {
      title: 'Курица с картошкой',
      needs: ['Курица', 'Картошка', 'Лук', 'Соль'],
      time: '60 мин',
      steps: ['Нарезать курицу и картошку.', 'Обжарить лук до золотистого цвета.', 'Добавить курицу, жарить 15 минут.', 'Добавить картошку, тушить под крышкой 30 минут.', 'Посолить, подавать горячим.']
    },
    {
      title: 'Яичница с помидорами',
      needs: ['Яйца', 'Помидор', 'Масло', 'Соль'],
      time: '10 мин',
      steps: ['Разогреть масло на сковороде.', 'Нарезать помидоры, обжарить 2 минуты.', 'Разбить яйца, жарить до готовности.', 'Посолить, подавать сразу.']
    },
    {
      title: 'Гречка с луком',
      needs: ['Гречка', 'Лук', 'Масло', 'Соль'],
      time: '25 мин',
      steps: ['Обжарить нарезанный лук до золотистого цвета.', 'Промыть гречку, залить водой 1:2.', 'Варить 20 минут на малом огне.', 'Смешать с луком, посолить.']
    },
    {
      title: 'Простой суп с курицей',
      needs: ['Курица', 'Морковь', 'Картошка', 'Лук', 'Соль'],
      time: '45 мин',
      steps: ['Поставить курицу вариться в 2 л воды.', 'Нарезать овощи.', 'Через 20 минут добавить овощи.', 'Варить ещё 25 минут.', 'Посолить, добавить зелень.']
    },
    {
      title: 'Макароны с сыром',
      needs: ['Макароны', 'Сыр', 'Масло', 'Соль'],
      time: '20 мин',
      steps: ['Сварить макароны до готовности.', 'Слить воду, добавить масло.', 'Натереть сыр, смешать с макаронами.', 'Подавать горячими.']
    },
    {
      title: 'Рыба в духовке',
      needs: ['Рыба', 'Лук', 'Соль', 'Перец'],
      time: '35 мин',
      steps: ['Разогреть духовку до 180°C.', 'Нарезать лук кольцами, выложить на противень.', 'Рыбу посолить и поперчить, выложить на лук.', 'Запекать 30 минут.']
    }
  ],

  init() {
    this.savedRecipes = Storage.get('savedRecipes', []);
    this.renderStalls();
    document.getElementById('findRecipesBtn').addEventListener('click', () => this.findRecipes());
    document.getElementById('recipeCellarBtn').addEventListener('click', () => this.showCellar());
  },

  renderStalls() {
    const container = document.getElementById('marketStalls');
    container.innerHTML = '';
    this.stalls.forEach(stall => {
      const stallEl = document.createElement('div');
      stallEl.className = 'market-stall';
      stallEl.innerHTML = `<div class="market-stall__name">${stall.name}</div>`;
      const itemsEl = document.createElement('div');
      itemsEl.className = 'market-stall__items';
      stall.items.forEach(item => {
        const btn = document.createElement('button');
        btn.className = 'market-ingredient' + (this.selectedIngredients.has(item) ? ' selected' : '');
        btn.textContent = item;
        btn.addEventListener('click', () => {
          if (this.selectedIngredients.has(item)) this.selectedIngredients.delete(item);
          else this.selectedIngredients.add(item);
          btn.classList.toggle('selected', this.selectedIngredients.has(item));
          this.updateBasket();
        });
        itemsEl.appendChild(btn);
      });
      stallEl.appendChild(itemsEl);
      container.appendChild(stallEl);
    });
  },

  updateBasket() {
    const el = document.getElementById('basketItems');
    el.textContent = this.selectedIngredients.size ? [...this.selectedIngredients].join(', ') : 'пусто';
  },

  findRecipes() {
    const selected = [...this.selectedIngredients];
    const container = document.getElementById('recipesScroll');
    container.innerHTML = '';

    if (!selected.length) {
      container.innerHTML = '<p style="color:#888;font-style:italic;">Выберите ингредиенты в корзину</p>';
      container.classList.remove('hidden');
      return;
    }

    const found = this.recipeDB.filter(r => r.needs.every(n => selected.includes(n) || !['Курица','Говядина','Свинина','Рыба','Яйца','Молоко'].includes(n)) || r.needs.filter(n => selected.includes(n)).length >= 2);

    if (!found.length) {
      container.innerHTML = '<p style="color:#888;font-style:italic;">Рецептов не найдено. Выберите ещё ингредиентов.</p>';
      container.classList.remove('hidden');
      return;
    }

    found.forEach(recipe => {
      const scroll = document.createElement('div');
      scroll.className = 'recipe-scroll';
      scroll.innerHTML = `
        <div class="recipe-scroll__title">${recipe.title}</div>
        <div class="recipe-scroll__time">⏱️ ${recipe.time}</div>
        <div class="recipe-scroll__steps">
          ${recipe.steps.map((s, i) => `<div class="recipe-step" data-num="${i+1}">${s}</div>`).join('')}
        </div>
        <button class="recipe-save-btn">📚 Сохранить</button>
      `;
      scroll.querySelector('.recipe-save-btn').addEventListener('click', () => {
        if (!this.savedRecipes.find(r => r.title === recipe.title)) {
          this.savedRecipes.push(recipe);
          Storage.set('savedRecipes', this.savedRecipes);
          alert(`«${recipe.title}» сохранён в погреб!`);
        } else {
          alert('Этот рецепт уже в погребе.');
        }
      });
      container.appendChild(scroll);
    });

    container.classList.remove('hidden');
  },

  showCellar() {
    if (!this.savedRecipes.length) {
      alert('Погреб пуст. Сохраните рецепты!');
      return;
    }
    const list = this.savedRecipes.map(r => `📜 ${r.title} (${r.time})`).join('\n');
    alert(`📚 Мой погреб:\n\n${list}`);
  }
};
