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
    <ul>
      {#each $cart as item}
        <li>
          {item.name} x {item.quantity} - ${item.sale_price * item.quantity}
          <button on:click={() => removeFromCart(item)}>Remove</button>
        </li>
      {/each}
    </ul>
    <p>Total: ${total}</p>
    <button on:click={checkout}>Checkout</button>
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
    height: 100%;
    width: 300px;
    transition: right 0.3s ease-in-out;
    z-index: 1000;
  }

  .cart-sidebar-open {
    right: 0;
  }

  .cart-sidebar h3 {
    margin-top: 0;
  }

  .cart-sidebar ul {
    list-style: none;
    padding: 0;
  }

  /* More specific styles here... */
</style>
