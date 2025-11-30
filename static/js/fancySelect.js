// static/js/fancySelect.js
(function () {
    function initFancySelects(root) {
        const scope = root || document;

        // evita reinicializar selects já processados
        const SELECT_SELECTOR = 'select[data-fancy="js fancy-select"]:not(.fancy-select-native)';
        const nativeSelects = scope.querySelectorAll(SELECT_SELECTOR);
        if (!nativeSelects.length) return;

        function closeAllExcept(exceptWrapper) {
            document.querySelectorAll('.fancy-select.is-open').forEach(fs => {
                if (fs !== exceptWrapper) {
                    fs.classList.remove('is-open');
                }
            });
        }

        nativeSelects.forEach(select => {
            const labelText = select.dataset.fancyLabel || select.getAttribute('aria-label') || '';
            const options = Array.from(select.options);
            const placeholderText = options[0]?.textContent || 'Selecione...';

            // wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'fancy-select';

            // se tiver data-fancy-up, força dropdown pra cima
            if (select.dataset.fancyUp === 'true' || select.hasAttribute('data-fancy-up')) {
                wrapper.classList.add('fancy-select--up');
            }

            // trigger
            const trigger = document.createElement('button');
            trigger.type = 'button';
            trigger.className = 'fancy-select-trigger';

            const inner = document.createElement('div');
            inner.className = 'fancy-select-trigger-inner';

            const valueWrapper = document.createElement('div');
            valueWrapper.className = 'fancy-select-value-wrapper';

            if (labelText) {
                const labelEl = document.createElement('span');
                labelEl.className = 'fancy-select-label';
                labelEl.textContent = labelText;
                valueWrapper.appendChild(labelEl);
            }

            const valueSpan = document.createElement('span');
            valueSpan.className = 'fancy-select-value is-placeholder';
            valueSpan.textContent = placeholderText;
            valueWrapper.appendChild(valueSpan);

            const arrowWrap = document.createElement('div');
            arrowWrap.className = 'fancy-select-arrow-wrapper';

            const arrowSpan = document.createElement('span');
            arrowSpan.className = 'fancy-select-arrow';
            arrowSpan.innerHTML = '&#9662;'; // ▼

            arrowWrap.appendChild(arrowSpan);

            inner.appendChild(valueWrapper);
            inner.appendChild(arrowWrap);
            trigger.appendChild(inner);

            // lista
            const list = document.createElement('ul');
            list.className = 'fancy-select-list';

            options.forEach(option => {
                const li = document.createElement('li');
                li.className = 'fancy-select-option';
                li.dataset.value = option.value;
                li.textContent = option.textContent;

                if (option.disabled) {
                    li.setAttribute('aria-disabled', 'true');
                }

                if (option.selected && option.value !== '') {
                    li.classList.add('is-selected');
                    valueSpan.textContent = option.textContent;
                    valueSpan.classList.remove('is-placeholder');
                    wrapper.classList.add('has-value');
                }

                list.appendChild(li);
            });

            if (!select.value) {
                valueSpan.textContent = placeholderText;
                valueSpan.classList.add('is-placeholder');
                wrapper.classList.remove('has-value');
            }

            // marca como inicializado e "esconde" o nativo
            select.classList.add('fancy-select-native');

            // monta DOM
            select.parentNode.insertBefore(wrapper, select);
            wrapper.appendChild(trigger);
            wrapper.appendChild(list);
            wrapper.appendChild(select);

            // eventos
            trigger.addEventListener('click', () => {
                const isOpen = wrapper.classList.contains('is-open');
                closeAllExcept(wrapper);
                if (!isOpen) {
                    wrapper.classList.add('is-open');
                } else {
                    wrapper.classList.remove('is-open');
                }
            });

            trigger.addEventListener('keydown', (ev) => {
                if (ev.key === 'Enter' || ev.key === ' ') {
                    ev.preventDefault();
                    trigger.click();
                }
            });

            list.addEventListener('click', (event) => {
                const optionEl = event.target.closest('.fancy-select-option');
                if (!optionEl || optionEl.getAttribute('aria-disabled') === 'true') {
                    return;
                }

                const newValue = optionEl.dataset.value;

                // atualiza select nativo
                select.value = newValue;
                select.dispatchEvent(new Event('change', { bubbles: true }));

                // visual
                list.querySelectorAll('.fancy-select-option')
                    .forEach(li => li.classList.remove('is-selected'));
                if (newValue !== '') {
                    optionEl.classList.add('is-selected');
                }

                if (!newValue) {
                    valueSpan.textContent = placeholderText;
                    valueSpan.classList.add('is-placeholder');
                    wrapper.classList.remove('has-value');
                } else {
                    valueSpan.textContent = optionEl.textContent;
                    valueSpan.classList.remove('is-placeholder');
                    wrapper.classList.add('has-value');
                }

                wrapper.classList.remove('is-open');
            });
        });

        // fecha ao clicar fora
        document.addEventListener('click', (e) => {
            const clickedFancy = e.target.closest('.fancy-select');
            document.querySelectorAll('.fancy-select.is-open').forEach(fs => {
                if (fs !== clickedFancy) {
                    fs.classList.remove('is-open');
                }
            });
        });
    }

    // expõe global
    window.initFancySelects = initFancySelects;

    // inicial padrão
    document.addEventListener("DOMContentLoaded", function () {
        initFancySelects(document);
    });
})();
