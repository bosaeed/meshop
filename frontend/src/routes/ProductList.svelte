<!-- meshop/frontend/src/routes/ProductList.svelte -->
<script>
  import { onMount } from "svelte";
  import { navigate } from "svelte-routing";
  import { fade } from 'svelte/transition';

  let products = [];
  let searchTerm = "";

  onMount(async () => {
    // Fetch products from API
    const response = await fetch("http://localhost:8000/products");
    products = await response.json();
  });

  $: filteredProducts = products.filter(product => 
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  function truncateDescription(description, maxLength = 50) {
    return description.length > maxLength 
      ? description.substring(0, maxLength) + '...' 
      : description;
  }

  function handleCardClick(productId) {
    navigate(`/product/${productId}`);
  }
</script>

<div class="product-list-container">
<div class="product-grid">
  {#each filteredProducts as product (product.id)}
    <div class="product" transition:fade on:click={() => handleCardClick(product.id)}>
      <div class="image-container">
        <img 
          src={product.images && product.images.length > 0 ? product.images[0] : '/placeholder.png'} 
          alt={product.name}
          loading="lazy"
        />
      </div>
      <h2>{product.name}</h2>
      <p>{truncateDescription(product.description)}</p>
      <p class="price">Price: ${product.sale_price}</p>
    </div>
  {/each}
</div>
</div>

<div class="search-container">
<input 
  type="text" 
  bind:value={searchTerm} 
  placeholder="Search products..."
/>
</div>

<style>
.product-list-container {
  padding-bottom: 60px; /* Make room for the fixed search box */
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(400px, 100%), 1fr));
  gap: 1rem;
}

.product {
  border: 1px solid #ccc;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  cursor: pointer;
  transition: box-shadow 0.3s ease;
  width: 100%;
}

.product:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.image-container {
  width: 100%;
  height: 300px;
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
}

.product p {
  margin: 0.5rem 0;
}

.price {
  font-weight: bold;
}

.search-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: white;
  padding: 1rem;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
}

input {
  width: 100%;
  padding: 0.5rem;
  font-size: 1rem;
}


@media (max-width: 400px) {
  .product-grid {
    grid-template-columns: 1fr;
  }
}
</style>