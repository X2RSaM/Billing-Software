document.addEventListener('DOMContentLoaded', () => {
    const addCustomerForm = document.getElementById('add-customer-form');
    const customerList = document.getElementById('customer-list');
    const addProductForm = document.getElementById('add-product-form');
    const productList = document.getElementById('product-list');
    const addBillingForm = document.getElementById('add-billing-form');
    const billingList = document.getElementById('billing-list');
    const billingProducts = document.getElementById('billing-products');
    const billingCustomer = document.getElementById('billing-customer');
    const totalSalesElement = document.getElementById('total-sales');
    const totalRevenueElement = document.getElementById('total-revenue');

    // Fetch and display customers
    function fetchCustomers() {
        fetch('/get_customers/')
            .then(response => response.json())
            .then(customers => {
                displayCustomers(customers);
                populateCustomerDropdown(customers);
            })
            .catch(error => console.error('Error fetching customers:', error));
    }

    function displayCustomers(customers) {
        customerList.innerHTML = '';
        customers.forEach(customer => {
            const div = document.createElement('div');
            div.className = 'customer-card';
            div.innerHTML = `
                <h3>${customer.name}</h3>
                <p>Gender: ${customer.gender}</p>
                <p>Contact: ${customer.contact}</p>
                <p>Email: ${customer.email}</p>
                <button onclick="editCustomer(${customer.id})">Edit</button>
                <button onclick="deleteCustomer(${customer.id})">Delete</button>
            `;
            customerList.appendChild(div);
        });
    }

    function populateCustomerDropdown(customers) {
        billingCustomer.innerHTML = '<option value="">Select a customer</option>';
        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = customer.name;
            billingCustomer.appendChild(option);
        });
    }

    addCustomerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const customerData = {
            name: document.getElementById('customer-name').value,
            gender: document.getElementById('customer-gender').value,
            contact: document.getElementById('customer-contact').value,
            email: document.getElementById('customer-email').value
        };
        fetch('/add_customer/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(customerData)
        })
        .then(response => response.json())
        .then(() => {
            fetchCustomers();
            addCustomerForm.reset();
        })
        .catch(error => console.error('Error adding customer:', error));
    });

    // Fetch and display products
    function fetchProducts() {
        fetch('/get_products/')
            .then(response => response.json())
            .then(products => {
                displayProducts(products);
                populateBillingProducts(products);
            })
            .catch(error => console.error('Error fetching products:', error));
    }

    function displayProducts(products) {
        productList.innerHTML = '';
        products.forEach(product => {
            const div = document.createElement('div');
            div.className = 'product-card';
            div.innerHTML = `
                <h3>${product.name}</h3>
                <p>Price: $${product.price}</p>
                <p>Quantity: ${product.quantity}</p>
                <p>Brand: ${product.brand}</p>
                <button onclick="editProduct(${product.id})">Edit</button>
                <button onclick="deleteProduct(${product.id})">Delete</button>
            `;
            productList.appendChild(div);
        });
    }

    function populateBillingProducts(products) {
        billingProducts.innerHTML = '';
        products.forEach(product => {
            const div = document.createElement('div');
            div.innerHTML = `
                <input type="checkbox" name="product" value="${product.id}">
                ${product.name} - $${product.price}
                <input type="number" name="quantity" min="1" value="1">
            `;
            billingProducts.appendChild(div);
        });
    }

    addProductForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const productData = {
            name: document.getElementById('product-name').value,
            price: parseFloat(document.getElementById('product-price').value),
            quantity: parseInt(document.getElementById('product-quantity').value),
            brand: document.getElementById('product-brand').value,
            supplier: document.getElementById('product-supplier').value,
            old_stock: parseInt(document.getElementById('product-old-stock').value),
            category: document.getElementById('product-category').value
        };
        fetch('/add_product/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        })
        .then(response => response.json())
        .then(() => {
            fetchProducts();
            addProductForm.reset();
        })
        .catch(error => console.error('Error adding product:', error));
    });

    addBillingForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const selectedProducts = [...document.querySelectorAll('input[name="product"]:checked')];
        const productIds = selectedProducts.map(input => input.value);
        const quantities = selectedProducts.map(input => input.nextElementSibling.nextElementSibling.value);

        const billingData = {
            customer_id: parseInt(billingCustomer.value),
            product_ids: productIds.map(id => parseInt(id)),
            quantities: quantities.map(qty => parseInt(qty))
        };

        fetch('/add_billing/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(billingData)
        })
        .then(response => response.json())
        .then(() => {
            fetchBilling();
            addBillingForm.reset();
        })
        .catch(error => console.error('Error adding billing:', error));
    });

    function fetchBilling() {
        fetch('/get_bills/')  // Add the appropriate endpoint for fetching bills if needed
            .then(response => response.json())
            .then(billings => {
                displayBillings(billings);
            })
            .catch(error => console.error('Error fetching billings:', error));
    }

    function displayBillings(billings) {
        billingList.innerHTML = '';
        billings.forEach(billing => {
            const div = document.createElement('div');
            div.className = 'billing-card';
            div.innerHTML = `
                <h3>Billing ID: ${billing.id}</h3>
                <p>Customer ID: ${billing.customer_id}</p>
                <p>Total Amount: $${billing.total_amount}</p>
                <button onclick="viewBill(${billing.id})">View Details</button>
            `;
            billingList.appendChild(div);
        });
    }

    function viewBill(billId) {
        fetch(`/get_bill/${billId}/`)
            .then(response => response.json())
            .then(bill => {
                // Display bill details or update UI accordingly
                console.log('Bill Details:', bill);
            })
            .catch(error => console.error('Error fetching bill details:', error));
    }

    // Initial data fetch
    fetchCustomers();
    fetchProducts();
});
