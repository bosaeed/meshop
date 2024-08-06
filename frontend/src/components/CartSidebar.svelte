<script>
  import { cart } from '../env';
  
  export let isOpen = false;

  let total = 0;
  
  // Subscribe to changes in the cart store
  $: { 
    cart.subscribe(items => {
      total = items.reduce((acc, item) => acc + (item.sale_price * item.quantity), 0);
    });
  }

  function removeFromCart(item) {
    cart.update(items => items.filter(i => i.id !== item.id));
  }

  function checkout() {
    console.log("Checkout process initiated");
  }
</script>

<aside class:cart-sidebar-open={isOpen} class="cart-sidebar">
    <h3>Cart</h3>
    {#if $cart.length === 0}
      <p>Your cart is empty.</p>
    {:else}
      <div class="cart-content">
        <div class="cart-items-container">
          <ul class="cart-items">
            {#each $cart as item}
              <li class="cart-item">
                <div class="item-info">
                  <span class="item-name">{item.name}</span>
                  <span class="item-quantity">x {item.quantity}</span>
                </div>
                <div class="item-price">${(item.sale_price * item.quantity).toFixed(2)}</div>
                <button class="remove-button" on:click={() => removeFromCart(item)}>Remove</button>
              </li>
            {/each}
          </ul>
        </div>
      </div>
      <div class="cart-summary">
        <div class="cart-total">
          <span>Total:</span>
          <span>${total.toFixed(2)}</span>
        </div>
        <button class="checkout-button" on:click={checkout}>Checkout</button>
      </div>
    {/if}
  </aside>

<style>
  .cart-sidebar {
    background-color: #f4f4f4;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: var(--box-shadow);
    position: fixed;
    right: -300px;
    top: 0;
    height: 90%;
    width: 300px;
    transition: right 0.3s ease-in-out;
    z-index: 1000;
    display: flex;
    flex-direction: column;
  }

  .cart-sidebar-open {
    right: 0;
  }

  .cart-sidebar h3 {
    margin-top: 0;
    margin-bottom: 1rem;
  }

  .cart-content {
    flex-grow: 1;
    overflow-y: auto;
    overflow-x: clip;
  }

  .cart-items {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .cart-item {
    display: grid;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #ddd;
  }

  .item-info {
    flex-grow: 1;
  }

  .item-name {
    font-weight: bold;
  }

  .item-quantity {
    color: #666;
    margin-left: 5px;
  }

  .item-price {
    font-weight: bold;
    margin: 0 10px;
  }

  .remove-button {
    background-color: #ff4444;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
  }

  .remove-button:hover {
    background-color: #cc0000;
  }

  .cart-summary {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 2px solid #333;
  }

  .cart-total {
    display: flex;
    justify-content: space-between;
    font-weight: bold;
    margin-bottom: 1rem;
  }

  .checkout-button {
    width: 100%;
    padding: 10px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
  }

  .checkout-button:hover {
    background-color: #45a049;
  }

</style>
