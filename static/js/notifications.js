// static/js/notifications.js
(function () {
    const DISPLAY_TIME = 4000;
    const ANIMATION_TIME = 250;
    let toastRoot = null;

    function ensureRoot() {
        if (toastRoot && document.body.contains(toastRoot)) return toastRoot;

        toastRoot = document.createElement('div');
        toastRoot.id = 'toast-root';
        toastRoot.className = 'toast-root';
        document.body.appendChild(toastRoot);
        return toastRoot;
    }

    // ========== TOAST SIMPLES ==========

    function createToastElement(notification) {
        const { title, text, variant = 'info' } = notification;

        const toast = document.createElement('div');
        toast.className = `toast toast--${variant}`;

        const content = document.createElement('div');
        content.className = 'toast-content';

        if (title) {
            const titleEl = document.createElement('div');
            titleEl.className = 'toast-title';
            titleEl.textContent = title;
            content.appendChild(titleEl);
        }

        if (text) {
            const textEl = document.createElement('div');
            textEl.className = 'toast-text';
            textEl.textContent = text;
            content.appendChild(textEl);
        }

        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => hideToast(toast));

        toast.appendChild(content);
        toast.appendChild(closeBtn);

        // Barra de progresso
        const bar = document.createElement('div');
        bar.className = 'toast-progress';
        toast.appendChild(bar);

        // anima progress bar
        requestAnimationFrame(() => {
            bar.style.transition = `width ${DISPLAY_TIME}ms linear`;
            bar.style.width = '0%';
        });

        return toast;
    }

    function showNotification(notification) {
        const root = ensureRoot();
        const toast = createToastElement(notification);

        // empilha um embaixo do outro (já funciona com seu CSS)
        root.insertBefore(toast, root.firstChild);

        requestAnimationFrame(() => {
            toast.classList.add('toast--visible');
        });

        const timeoutId = setTimeout(() => {
            hideToast(toast);
        }, DISPLAY_TIME + ANIMATION_TIME);

        toast.dataset.timeoutId = timeoutId;
    }

    function hideToast(toast) {
        if (!toast) return;

        const id = toast.dataset.timeoutId;
        if (id) clearTimeout(parseInt(id, 10));

        toast.classList.remove('toast--visible');
        toast.classList.add('toast--hiding');

        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, ANIMATION_TIME);
    }

    // API pública de notificação simples
    window.enqueueNotification = function enqueueNotification(notification) {
        if (!notification) return;
        showNotification(notification);
    };

    window.displayQueuedNotifications = function displayQueuedNotifications() {
        // mantido por compat – não faz nada
    };

    // ========== CONFIRM GENÉRICO (showConfirm) ==========

    window.showConfirm = function showConfirm(options) {
        const {
            title = "Confirmação",
            text = "Tem certeza?",
            confirmLabel = "Confirmar",
            cancelLabel = "Cancelar",
            variant = "info", // "info", "warning", "error", "success"
        } = options || {};

        return new Promise((resolve) => {
            // overlay centralizado
            const overlay = document.createElement('div');
            overlay.className = 'confirm-overlay';

            // caixinha do confirm
            const box = document.createElement('div');
            box.className = `confirm-modal confirm-modal--${variant}`;

            const titleEl = document.createElement('div');
            titleEl.className = 'confirm-title';
            titleEl.textContent = title;

            const textEl = document.createElement('div');
            textEl.className = 'confirm-text';
            textEl.textContent = text;

            const actions = document.createElement('div');
            actions.className = 'confirm-actions';

            const btnCancel = document.createElement('button');
            btnCancel.type = 'button';
            btnCancel.className = 'btn ghost';      // respeita seu btn.ghost azul claro
            btnCancel.textContent = cancelLabel;

            const btnConfirm = document.createElement('button');
            btnConfirm.type = 'button';
            btnConfirm.className = 'btn primary';   // botão azul principal
            btnConfirm.textContent = confirmLabel;

            actions.appendChild(btnCancel);
            actions.appendChild(btnConfirm);

            box.appendChild(titleEl);
            box.appendChild(textEl);
            box.appendChild(actions);

            overlay.appendChild(box);
            document.body.appendChild(overlay);

            function clean(result) {
                document.removeEventListener('keydown', handleKey);
                overlay.classList.add('confirm-overlay--hiding');
                setTimeout(() => {
                    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
                    resolve(result);
                }, 200);
            }

            function handleKey(e) {
                if (e.key === 'Escape') {
                    clean(false);
                }
            }

            btnCancel.addEventListener('click', () => clean(false));
            btnConfirm.addEventListener('click', () => clean(true));

            document.addEventListener('keydown', handleKey);
        });
    };
})();
