// static/js/card-filter.js
(function () {
    function resolveElement(ref) {
        if (!ref) return null;
        if (ref instanceof Element) return ref;
        if (typeof ref === "string") return document.querySelector(ref);
        return null;
    }

    // Gera lista de páginas mostrando sempre primeira, última e vizinhas da atual
    function buildPageRange(totalPages, currentPage, maxButtons) {
        const pages = [];

        if (totalPages <= maxButtons) {
            for (let i = 1; i <= totalPages; i++) pages.push(i);
            return pages;
        }

        const set = new Set();
        set.add(1);
        set.add(totalPages);
        set.add(currentPage);

        if (currentPage > 1) set.add(currentPage - 1);
        if (currentPage < totalPages) set.add(currentPage + 1);

        let offset = 2;
        const targetSize = Math.min(maxButtons, totalPages);

        while (set.size < targetSize) {
            const left = currentPage - offset;
            const right = currentPage + offset;

            if (left > 1) set.add(left);
            if (set.size >= targetSize) break;

            if (right < totalPages) set.add(right);
            if (set.size >= targetSize) break;

            if (left <= 1 && right >= totalPages) break;
            offset++;
        }

        return Array.from(set).sort((a, b) => a - b);
    }

    window.initCardFilter = function initCardFilter(options) {
        const {
            container,        // '#dup-groups'
            itemSelector,     // '.duplicate-group'
            controls,         // '#dup-pagination'
            perPage = 10,
            perPageOptions = [10, 20, 50],
            searchInput,      // opcional
            searchAttrs = ['data-nome', 'data-carro'],
            emptySelector,    // opcional
            customFilter,     // opcional: function(item) => boolean
            onStatsChange,    // opcional: callback com info de página
        } = options || {};

        const containerEl = resolveElement(container);
        const controlsEl  = resolveElement(controls);
        const searchEl    = resolveElement(searchInput);
        const emptyEl     = resolveElement(emptySelector);

        if (!containerEl || !controlsEl || !itemSelector) {
            console.warn("initCardFilter: container / controls / itemSelector inválidos");
            return null;
        }

        let allItems = Array.from(containerEl.querySelectorAll(itemSelector));
        if (!allItems.length) {
            console.warn("initCardFilter: nenhum item encontrado para", itemSelector);
            return null;
        }

        let currentPage   = 1;
        let pageSize      = perPage;
        let visibleItems  = allItems.slice();
        let totalPages    = Math.max(1, Math.ceil(visibleItems.length / pageSize));
        let extraFilter   = (typeof customFilter === "function") ? customFilter : null;

        // -------------------------------------
        // Monta HTML dos controles de paginação
        // -------------------------------------
        const optionsHtml = (perPageOptions && perPageOptions.length ? perPageOptions : [perPage])
            .map(val => {
                const selected = val === perPage ? "selected" : "";
                return `<option value="${val}" ${selected}>${val} Grupos</option>`;
            })
            .join("");

        controlsEl.innerHTML = `
            <div class="card-filter-controls">
                <div class="card-filter-perpage">
                    <select
                        class="input"
                        data-fancy="js fancy-select"
                        data-fancy-label="Itens"
                        data-fancy-up="true"
                        data-role="per-page-select"
                    >
                        ${optionsHtml}
                    </select>
                </div>

                <div class="card-pagination">
                    <button
                        type="button"
                        class="btn btn-sm card-page-btn card-page-btn-arrow"
                        data-role="prev"
                    >
                        &#x2039;
                    </button>

                    <div class="card-page-numbers" data-role="pages"></div>

                    <button
                        type="button"
                        class="btn btn-sm card-page-btn card-page-btn-arrow"
                        data-role="next"
                    >
                        &#x203A;
                    </button>
                </div>
            </div>
        `;

        const perPageSelect = controlsEl.querySelector('[data-role="per-page-select"]');
        const btnPrev       = controlsEl.querySelector('[data-role="prev"]');
        const btnNext       = controlsEl.querySelector('[data-role="next"]');
        const pagesContainer= controlsEl.querySelector('[data-role="pages"]');

        // aplica fancy select nos controles recém-criados
        if (typeof window.initFancySelects === "function") {
            window.initFancySelects(controlsEl);
        }

        if (!perPageSelect || !btnPrev || !btnNext || !pagesContainer) {
            console.warn("initCardFilter: falha ao montar controles de paginação");
            return null;
        }

        // ------------------------
        // Funções internas
        // ------------------------
        function updateEmptyState() {
            if (!emptyEl) return;
            const hasVisible = visibleItems.length > 0;
            emptyEl.style.display = hasVisible ? "none" : "";
        }

        function emitStats(sliceLength, startIndex) {
            if (typeof onStatsChange !== "function") return;

            const filteredTotal = visibleItems.length;
            const pageFrom = filteredTotal === 0 ? 0 : (startIndex + 1);
            const pageTo   = startIndex + sliceLength;

            onStatsChange({
                currentPage,
                pageSize,
                totalItems: allItems.length,
                filteredTotal,
                pageFrom,
                pageTo,
                pageCount: totalPages,
                pageItems: sliceLength,
            });
        }

        function renderPage() {
            allItems.forEach(it => { it.style.display = "none"; });

            if (!visibleItems.length) {
                updateEmptyState();
                btnPrev.disabled = true;
                btnNext.disabled = true;
                emitStats(0, 0);
                return;
            }

            const start = (currentPage - 1) * pageSize;
            const end   = start + pageSize;
            const slice = visibleItems.slice(start, end);

            slice.forEach(it => { it.style.display = ""; });

            updateEmptyState();

            btnPrev.disabled = currentPage <= 1;
            btnNext.disabled = currentPage >= totalPages;

            emitStats(slice.length, start);
        }

        function renderPager() {
            pagesContainer.innerHTML = "";

            if (totalPages <= 1) {
                btnPrev.disabled = true;
                btnNext.disabled = true;
                return;
            }

            const maxButtons = 6;
            const pageList = buildPageRange(totalPages, currentPage, maxButtons);

            pageList.forEach(page => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = "btn btn-sm card-page-btn";
                btn.textContent = page;

                if (page === currentPage) {
                    btn.classList.add("is-active");
                }

                btn.addEventListener("click", () => {
                    if (page === currentPage) return;
                    currentPage = page;
                    renderPage();
                    renderPager();
                });

                pagesContainer.appendChild(btn);
            });
        }

        function applyFilters() {
            const query = searchEl ? (searchEl.value || "").trim().toLowerCase() : "";

            visibleItems = [];
            allItems.forEach(item => {
                let matches = true;

                if (query) {
                    matches = searchAttrs.some(attr => {
                        if (!attr) return false;
                        const val = item.getAttribute(attr) || "";
                        return val.toLowerCase().includes(query);
                    });
                }

                if (matches && typeof extraFilter === "function") {
                    matches = !!extraFilter(item);
                }

                if (matches) {
                    visibleItems.push(item);
                }
            });

            totalPages = Math.max(1, Math.ceil(visibleItems.length / pageSize));
            if (currentPage > totalPages) currentPage = 1;

            renderPage();
            renderPager();
        }

        // ------------------------
        // Eventos
        // ------------------------
        perPageSelect.addEventListener("change", function () {
            const value = parseInt(this.value, 10);
            if (!value || value <= 0) return;
            pageSize = value;
            currentPage = 1;
            totalPages = Math.max(1, Math.ceil(visibleItems.length / pageSize));
            renderPage();
            renderPager();
        });

        btnPrev.addEventListener("click", () => {
            if (currentPage <= 1) return;
            currentPage -= 1;
            renderPage();
            renderPager();
        });

        btnNext.addEventListener("click", () => {
            if (currentPage >= totalPages) return;
            currentPage += 1;
            renderPage();
            renderPager();
        });

        if (searchEl) {
            searchEl.addEventListener("input", () => {
                currentPage = 1;
                applyFilters();
            });
        }

        // ------------------------
        // Inicializa sempre na página 1
        // ------------------------
        currentPage = 1;
        applyFilters();

        // API pública
        return {
            refresh() {
                allItems = Array.from(containerEl.querySelectorAll(itemSelector));
                visibleItems = allItems.slice();
                currentPage = 1;
                totalPages = Math.max(1, Math.ceil(visibleItems.length / pageSize));
                applyFilters();
            },
            setCustomFilter(fn) {
                extraFilter = (typeof fn === "function") ? fn : null;
                currentPage = 1;
                applyFilters();
            }
        };
    };
})();
