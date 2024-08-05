<!-- meshop/frontend/src/routes/ProductDetail.svelte -->
<script>
  import { onMount } from "svelte";
    import { env } from '../env'
  export let id;

  let product = null;
  let selectedImage = null;

  onMount(async () => {
    // Fetch product details from API
    const response = await fetch(`${env.BACKEND_URL}/products/${id}`);
    product = await response.json();
    if (product && product.images && product.images.length > 0) {
      selectedImage = product.images[0];
    }
  });

  function selectImage(image) {
    selectedImage = image;
  }

  function addToCart() {
    // Implement add to cart functionality
    alert("Product added to cart!");
  }
</script>

<style>
  .product-detail {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
    padding: 20px;
    max-width: 80%; 
    margin: 0 auto;
    gap: 20px;
  }

  .main-image, .product-info {
    flex: 1 1 40%; 
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .main-image img {
    max-width: 100%;
    max-height: 500px;
    border-radius: 10px;
    object-fit: contain;
    margin-bottom: 10px;
  }

  .thumbnails {
    display: flex;
    justify-content: center;
    gap: 10px;
  }

  .thumbnails img {
    width: 70px;
    height: 70px;
    border-radius: 5px;
    cursor: pointer;
    object-fit: cover;
    border: 2px solid transparent;
  }

  .thumbnails img.selected {
    border-color: #007bff;
  }

  .product-info h1 {
    font-size: 2.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .product-info p {
    font-size: 1.3rem;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .product-info .price {
    font-weight: bold;
    font-size: 1.7rem;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .add-to-cart-btn {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .add-to-cart-btn:hover {
    background-color: #0056b3;
  }

  @media (max-width: 768px) {
    .product-detail {
      flex-direction: column;
      align-items: center;
    }

    .main-image, .product-info {
      flex: 1 1 100%; /* Full width on mobile screens */
    }
  }
</style>

{#if product}
  <div class="product-detail">
    <div class="main-image">
      <img src={selectedImage} alt={product.name} />
      <div class="thumbnails">
        {#each product.images as image (image)}
          <img
            src={image}
            alt="Thumbnail"
            class:selected={selectedImage === image}
            on:click={() => selectImage(image)}
          />
        {/each}
      </div>
    </div>
    <div class="product-info">
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <p class="price">Price: ${product.sale_price}</p>
      <button class="add-to-cart-btn" on:click={addToCart}>Add to Cart</button>
    </div>
  </div>
{:else}
  <p>Loading product...</p>
{/if}