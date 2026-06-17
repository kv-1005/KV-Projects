/**
 * Smart Autocomplete for Invoice Generator
 * 
 * Features:
 * - Debounced API searching
 * - Keyboard navigation
 * - Auto-filling of related fields (HSN, Price, Tax)
 * - "Premium" UI/UX
 */

class SmartAutocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = Object.assign({
            apiEndpoint: '/api/items/search',
            relatedFields: {
                hsn: 'hsn_code',
                price: 'unit_price',
                tax: 'tax_rate'
            },
            minChars: 2,
            debounceTime: 300,
            maxResults: 10
        }, options);

        this.debounceTimer = null;
        this.currentFocus = -1;
        this.searchResults = [];

        this.init();
    }

    init() {
        // Create container if not exists
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'autocomplete-wrapper';
        this.input.parentNode.insertBefore(this.wrapper, this.input);
        this.wrapper.appendChild(this.input);

        // Create dropdown container
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'autocomplete-dropdown';
        this.wrapper.appendChild(this.dropdown);

        // Event listeners
        this.input.addEventListener('input', (e) => this.onInput(e));
        this.input.addEventListener('keydown', (e) => this.onKeyDown(e));

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target !== this.input && e.target !== this.dropdown) {
                this.closeDropdown();
            }
        });

        // Add styles if not present
        if (!document.getElementById('autocomplete-styles')) {
            this.injectStyles();
        }
    }

    injectStyles() {
        const style = document.createElement('style');
        style.id = 'autocomplete-styles';
        style.textContent = `
            .autocomplete-wrapper {
                position: relative;
                width: 100%;
            }
            .autocomplete-dropdown {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 0 0 12px 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                z-index: 1000;
                max-height: 300px;
                overflow-y: auto;
                display: none;
                opacity: 0;
                transform: translateY(-10px);
                transition: all 0.2s cubic-bezier(0.165, 0.84, 0.44, 1);
            }
            .autocomplete-dropdown.show {
                display: block;
                opacity: 1;
                transform: translateY(0);
            }
            .autocomplete-item {
                padding: 12px 20px;
                cursor: pointer;
                border-bottom: 1px solid rgba(0,0,0,0.03);
                transition: background 0.1s ease;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .autocomplete-item:last-child {
                border-bottom: none;
            }
            .autocomplete-item:hover, .autocomplete-item.active {
                background-color: #f0f7ff;
                border-left: 3px solid #3498db;
                padding-left: 17px; /* Compensate for border */
            }
            .item-main {
                font-weight: 500;
                color: #2c3e50;
                font-size: 16px;
            }
            .item-meta {
                font-size: 13px;
                color: #7f8c8d;
                text-align: right;
            }
            .item-badge {
                display: inline-block;
                padding: 2px 6px;
                border-radius: 4px;
                background: #eef2f7;
                font-size: 11px;
                margin-left: 8px;
                color: #555;
            }
        `;
        document.head.appendChild(style);
    }

    onInput(e) {
        const val = this.input.value;

        clearTimeout(this.debounceTimer);
        this.closeDropdown();

        if (!val || val.length < this.options.minChars) return;

        this.debounceTimer = setTimeout(() => {
            this.fetchSuggestions(val);
        }, this.options.debounceTime);
    }

    async fetchSuggestions(query) {
        try {
            const response = await fetch(`${this.options.apiEndpoint}?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('API Error');

            const data = await response.json();
            this.renderSuggestions(data);
        } catch (error) {
            console.error('Autocomplete fetch error:', error);
        }
    }

    renderSuggestions(items) {
        if (!items.length) {
            this.closeDropdown();
            return;
        }

        this.searchResults = items;
        this.dropdown.innerHTML = '';

        items.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'autocomplete-item';

            // Smart labeling
            const priceHtml = item.unit_price > 0
                ? `<span class="item-badge">₹${item.unit_price.toLocaleString('en-IN')}</span>`
                : '';
            const hsnHtml = item.hsn_code
                ? `<span class="item-badge">HSN: ${item.hsn_code}</span>`
                : '';

            div.innerHTML = `
                <div class="item-main">
                    ${this.highlightMatch(item.label, this.input.value)}
                </div>
                <div class="item-meta">
                    ${hsnHtml}
                    ${priceHtml}
                </div>
            `;

            div.addEventListener('click', () => {
                this.selectItem(item);
            });

            this.dropdown.appendChild(div);
        });

        this.dropdown.classList.add('show');
    }

    highlightMatch(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    onKeyDown(e) {
        if (!this.dropdown.classList.contains('show')) return;

        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            this.currentFocus++;
            this.addActive(items);
        } else if (e.key === 'ArrowUp') {
            this.currentFocus--;
            this.addActive(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (this.currentFocus > -1) {
                if (items[this.currentFocus]) items[this.currentFocus].click();
            }
        } else if (e.key === 'Escape') {
            this.closeDropdown();
        }
    }

    addActive(items) {
        if (!items) return;
        this.removeActive(items);

        if (this.currentFocus >= items.length) this.currentFocus = 0;
        if (this.currentFocus < 0) this.currentFocus = (items.length - 1);

        items[this.currentFocus].classList.add('active');
        items[this.currentFocus].scrollIntoView({ block: 'nearest' });
    }

    removeActive(items) {
        for (let i = 0; i < items.length; i++) {
            items[i].classList.remove('active');
        }
    }

    closeDropdown() {
        this.dropdown.classList.remove('show');
        this.currentFocus = -1;
    }

    selectItem(item) {
        // Fill description
        this.input.value = item.value;
        this.closeDropdown();

        // Smart Fill Related Fields
        this.fillField('hsn', item.hsn_code);
        this.fillField('price', item.unit_price);
        this.fillField('tax', item.tax_rate);

        // Flash effect to show user something happened
        this.input.style.backgroundColor = '#e8f5e9';
        setTimeout(() => {
            this.input.style.backgroundColor = '';
        }, 500);
    }

    fillField(type, value) {
        if (!value && value !== 0) return;

        // Try to find the field by ID
        const fieldId = this.options.relatedFields[type];
        const field = document.getElementById(fieldId);

        if (field) {
            field.value = value;
            // Trigger change event for any listeners (like total calculators)
            field.dispatchEvent(new Event('change', { bubbles: true }));
            field.dispatchEvent(new Event('input', { bubbles: true }));

            // Flash effect
            const originalBg = field.style.backgroundColor;
            field.style.transition = 'background-color 0.3s';
            field.style.backgroundColor = '#e8f5e9'; // Light green
            setTimeout(() => {
                field.style.backgroundColor = originalBg;
            }, 800);
        }
    }
}

// Auto-initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    // We look for the standard #description field in "Add Item" forms
    const descInput = document.getElementById('description');
    if (descInput) {
        console.log('Automplete initialized for #description');
        new SmartAutocomplete(descInput, {
            relatedFields: {
                hsn: 'hsn_code',
                price: 'unit_price',
                tax: 'tax_rate'
            }
        });
    }

    // Also support editing existing items if they use inputs with specific classes? 
    // Usually inline edits (like in the modal) have different IDs.
    // Let's hook into the Edit Item Modal inputs as well if they exist
    const editDescInput = document.getElementById('edit_description');
    if (editDescInput) {
        console.log('Automplete initialized for #edit_description');
        new SmartAutocomplete(editDescInput, {
            relatedFields: {
                hsn: 'edit_hsn_code',
                price: 'edit_unit_price',
                tax: 'edit_tax_rate'
            }
        });
    }
});
