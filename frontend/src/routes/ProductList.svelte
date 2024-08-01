<script>
  import { onMount, onDestroy } from "svelte";
  import { navigate } from "svelte-routing";
  import { fade } from 'svelte/transition';

  let products = [];
  let searchTerm = "";
  let websocket;
  let isRecording = false;
  let audioLevel = 0;

  onMount(async () => {
    const response = await fetch("http://localhost:8000/products");
    products = await response.json();

    websocket = new WebSocket('ws://localhost:8000/ws'); 

    websocket.onmessage = (event) => {
      const recommendations = JSON.parse(event.data);
      console.log('Recommendations:', recommendations);
    };
  });

  $: filteredProducts = products.filter(product => 
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  $: if (websocket && searchTerm) {
    websocket.send(JSON.stringify({ user_input: searchTerm }));
  }

  function truncateDescription(description, maxLength = 50) {
    return description.length > maxLength 
      ? description.substring(0, maxLength) + '...' 
      : description;
  }

  function handleCardClick(productId) {
    navigate(`/product/${productId}`);
  }

  function startVoiceSearch() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();

    isRecording = true;

    recognition.onresult = (event) => {
      const speechResult = event.results[0][0].transcript;
      console.log('Speech result:', speechResult);
      searchTerm = speechResult;
    };

    recognition.onspeechend = () => {
      recognition.stop();
      console.log('onspeechend');
      isRecording = false;
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      isRecording = false;
    };

    recognition.onaudiostart = () => {
      console.log('onaudiostart');
      isRecording = true;
    };

    recognition.onaudioend = () => {
      console.log('onaudioend');
      isRecording = false;
    };

    recognition.onnomatch = () => {
      console.log('onnomatch');
      isRecording = false;
    };

    recognition.onstart = () => {
      console.log('onstart');
      isRecording = true;
    };

    recognition.onend = () => {
      console.log('onend');
      isRecording = false;
    };
  }

  onDestroy(() => {
    if (websocket) {
      websocket.close();
    }
  });
</script>

<div class="product-list-container">
  <div class="product-grid">
    {#each filteredProducts as product (product.id)}
      <div class="product" transition:fade on:click={() => handleCardClick(product.id)}>
        <div class="image-container">
          <img src={product.images && product.images.length > 0 ? product.images[0] : '/placeholder.jpeg'} alt={product.name} loading="lazy" />
        </div>
        <h2>{product.name}</h2>
        <p>{truncateDescription(product.description)}</p>
        <p class="price">Price: ${product.sale_price}</p>
      </div>
    {/each}
  </div>
</div>

<div class="search-container">
  <input type="text" bind:value={searchTerm} placeholder="Search products..." />
  <button on:click={startVoiceSearch}>🎤</button>
  {#if isRecording}
    <div class="feedback-wave"></div>
  {/if}
</div>

<style>
  .product-list-container {
    padding-bottom: 60px;
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
    background-color: white;
    border-radius: 8px;
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
    font-size: 1.2rem;
  }

  .product p {
    margin: 0.5rem 0;
  }

  .price {
    font-weight: bold;
    color: var(--primary-color);
  }

  .search-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: white;
    padding: 1rem;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
  }

  input {
    width: 100%;
    padding: 0.5rem;
    font-size: 1rem;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
    border-radius: 4px;
  }

  button:hover {
    background-color: var(--secondary-color);
  }

  .feedback-wave {
    width: 20px;
    height: 20px;
    background-color: var(--primary-color);
    border-radius: 50%;
    animation: wave 1s infinite;
  }

  @keyframes wave {
    0% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(2);
      opacity: 0.5;
    }
    100% {
      transform: scale(1);
      opacity: 1;
    }
  }
</style>