<script>
    import { createEventDispatcher } from 'svelte';
  export let product;
  export let onClick;

  const dispatch = createEventDispatcher();

  function truncateDescription(description, maxLength = 50) {
    return description.length > maxLength ? description.substring(0, maxLength) + '...' : description;
  }

  function handleClick() {
    onClick(product);
  }
</script>

<div class="product" class:glow={product.score > 0.6} on:click={handleClick} on:keydown={handleClick}  tabindex="-2">
  <div class="image-container">
    <img src={product.images && product.images.length > 0 ? product.images[0] : '/placeholder.jpeg'} alt={product.name} loading="lazy" />
  </div>
  <h2>{product.name}</h2>
  <p>{truncateDescription(product.description)}</p>
  <p class="price">Price: ${product.sale_price}</p>
  <button on:click="{() => dispatch('addToCart', product)}">Add to Cart</button>
</div>

<style>
  .product {
    border: 1px solid #e0e0e0;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    background-color: white;
    border-radius: 8px;
    box-shadow: var(--box-shadow);
  }

  .product.glow {
    box-shadow: 0 4px 8px rgba(0, 255, 0, 0.5);
  }

  .product:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    transform: translateY(-4px);
  }

  .image-container {
    width: 100%;
    height: 200px;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    margin-bottom: 1rem;
  }

  .product img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .product h2 {
    margin: 0.5rem 0;
    font-size: 0.7rem;
  }

  .product p {
    margin: 0.5rem 0;
    font-size: 0.5rem;
  }

  .price {
    font-weight: bold;
    color: var(--primary-color);
  }
</style>
