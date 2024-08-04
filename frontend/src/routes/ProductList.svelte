<script>
  import { onMount, onDestroy } from "svelte";
  import { navigate } from "svelte-routing";
  import { fade, fly } from 'svelte/transition';
  import { flip } from 'svelte/animate';

  let products = [];
  let searchTerm = "";
  let websocket;
  let isRecording = false;
  let isLoading = false;
  let isWebSocketConnected = false;
  let connectionAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 50;
  const RECONNECT_INTERVAL = 5000; // 5 seconds


  let toasts = [];

  let last_sent_message = ""

  function addToast(message, type = 'info') {
    const id = Date.now() + (Math.random() * 100);
    toasts = [...toasts, { id, message, type }];
    setTimeout(() => {
      removeToast(id);
    }, 3000);
  }

  function removeToast(id) {
    toasts = toasts.filter(toast => toast.id !== id);
  }



  function connectWebSocket() {
    websocket = new WebSocket('ws://localhost:8000/ws');

      websocket.onopen = () => {
      console.log('WebSocket connected');
      isWebSocketConnected = true;
      connectionAttempts = 0;
      addToast('WebSocket connected', 'success');
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      isWebSocketConnected = false;
      addToast('WebSocket disconnected', 'error');
      retryConnection();
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      isWebSocketConnected = false;
      addToast('WebSocket error', 'error');
    };


    websocket.onmessage = (event) => {
      const newRecommendations = JSON.parse(event.data);
      console.log('Recommendations:', newRecommendations);
      if('error' in newRecommendations) {
        console.error('Error:', newRecommendations.error)
      }
      else if( newRecommendations.action.toLowerCase() == 'recommend') {
        updateProducts(newRecommendations.products);
      }
      else if(newRecommendations.action.toLowerCase() == 'add_to_cart' ) {
        console.log('Add to cart:', newRecommendations.cart_items);
      }
      else if( newRecommendations.action.toLowerCase() == 'more_info') {
        console.log('more_info:', newRecommendations.product);
      }
      isLoading = false;
    };
  }

  function retryConnection() {
    if (connectionAttempts < MAX_RECONNECT_ATTEMPTS) {
      connectionAttempts++;
      console.log(`Attempting to reconnect (${connectionAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
      addToast(`Reconnecting... Attempt ${connectionAttempts}/${MAX_RECONNECT_ATTEMPTS}`, 'info');
      setTimeout(connectWebSocket, RECONNECT_INTERVAL);
    } else {
      console.error('Max reconnection attempts reached. Please refresh the page.');
      addToast('Max reconnection attempts reached. Please refresh the page.', 'error');
    }
  }

  onMount(() => {
    connectWebSocket();
  });

  onDestroy(() => {
    if (websocket) {
      websocket.close();
    }
  });

  function updateProducts(newProducts) {
    const delay = 100; // Delay between each product animation
    newProducts.forEach((product, index) => {
      setTimeout(() => {
        products = [...products.filter(p => p.id !== product.id), product];
      }, index * delay);
    });

    // Remove products that are not in the new list
    setTimeout(() => {
      products = products.filter(p => newProducts.some(np => np.id === p.id));
    }, newProducts.length * delay);
  }

  function debounce(fn, delay) {
    let timeoutID;
    return function (...args) {
      clearTimeout(timeoutID);
      timeoutID = setTimeout(() => {
        fn(...args);
      }, delay);
    };
  }

  function sendWebSocketMessage(message) {
    if (websocket && websocket.readyState == WebSocket.OPEN) {
      websocket.send(message);
      console.log('Sent message:', message);
      last_sent_message = searchTerm;

      isLoading = true;
    }
    else{
      console.error('Web socket not connected!');
    }
  }

  const debouncedSendWebSocketMessage = debounce(sendWebSocketMessage, 1000);

  $: if (websocket && searchTerm.length >= 3 && last_sent_message != searchTerm) {

    debouncedSendWebSocketMessage(JSON.stringify({ user_input: searchTerm }));
  }

  function truncateDescription(description, maxLength = 50) {
    return description.length > maxLength 
      ? description.substring(0, maxLength) + '...' 
      : description;
  }

  function handleCardClick(productId) {
    navigate(`/product/${productId}`);
  }



async function startVoiceSearch2() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
mediaRecorder.addEventListener('dataavailable', async (event) => {
  if (event.data.size > 0 && websocket.readyState === 1) {
    websocket.send(event.data);
  }
});
mediaRecorder.start(250); // send audio every 250ms
  
}


  function startVoiceSearch() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();



    isRecording = true;

    recognition.onresult = (event) => {
      console.log('Speech recognition event:', event)
      console.log('Speech recognition result:', event.results)
      const speechResult = event.results[event.results.length -1][0].transcript;
      console.log('Speech result:', speechResult);
      sendWebSocketMessage(speechResult)
      // websocket.send(JSON.stringify({ user_voice_input: speechResult }));
      searchTerm = speechResult;
      isLoading = true;
    };

    recognition.onspeechend = () => {
      recognition.stop();
      isRecording = false;
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      isRecording = false;
    };

    recognition.onend = () => {
      recognition.start();
      isRecording = false;
    };
  }
  function getProductSize(score) {
    if (!score) return 'normal';
    if (score > 0.8) return 'xl';
    if (score > 0.6) return 'large';
    if (score > 0.4) return 'medium';
    return 'normal';
  }
</script>

<div class="container {products.length === 0 ? 'dark-overlay' : ''}">
  <div class="connection-status {isWebSocketConnected ? 'connected' : 'disconnected'}"></div>
  
  {#if products.length === 0}
    <div class="centered-search">
      <h2>Find Your Perfect Product</h2>
      <div class="search-container large">
        <input type="text" bind:value={searchTerm} placeholder="Start by typing here..." />
        <button on:click={startVoiceSearch}>🎤</button>
        <div class="glowing-circle {isWebSocketConnected ? 'connected' : 'disconnected'}"></div>
      </div>
      {#if isRecording}
        <div class="feedback-wave"></div>
      {/if}
      {#if isLoading}
        <div class="loading-animation"></div>
      {/if}
    </div>
  {:else}
    <div class="product-list-container">
      <div class="product-list-container"> 
        <div class="product-grid"> 
          {#each products as product (product.id)} 
          <div animate:flip={{ duration: 300 }}> 
            <div class="product {getProductSize(product.score)}" class:glow={product.score > 0.6} in:fly={{ y: 50, duration: 300, delay: 300 }} out:fade={{ duration: 300 }} on:click={() => handleCardClick(product.id)}> 
              <div class="image-container"> 
                <img src={product.images && product.images.length > 0 ? product.images[0] : '/placeholder.jpeg'} alt={product.name} loading="lazy" /> 
              </div> <h2>{product.name}</h2> 
              <p>{truncateDescription(product.description)}</p> 
              <p class="price">Price: ${product.sale_price}</p> 
              {#if product.score} <p class="score">Score: {(product.score * 100).toFixed(0)}%</p> {/if} 
            </div> 
          </div> 
          {/each} 
        </div> 
      </div>
    </div>
    <div class="search-container bottom">
      <input type="text" bind:value={searchTerm} placeholder="Search products..." />
      <button on:click={startVoiceSearch}>🎤</button>
      <div class="glowing-circle {isWebSocketConnected ? 'connected' : 'disconnected'}"></div>
      {#if isRecording}
        <div class="feedback-wave"></div>
      {/if}
      {#if isLoading}
        <div class="loading-animation"></div>
      {/if}
    </div>
  {/if}
</div>

<div class="toast-container">
  {#each toasts as toast (toast.id)}
    <div class="toast {toast.type}" transition:fly="{{ y: 50, duration: 300 }}">
      {toast.message}
    </div>
  {/each}
</div>

<style>
  .container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .dark-overlay {
    background-color: rgba(0, 0, 0, 0.8);
  }

  .centered-search {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    color: white;
  }

  .centered-search h2 {
    margin-bottom: 2rem;
    font-size: 2.5rem;
    text-align: center;
  }

  .product-list-container {
    flex-grow: 1;
    padding: 1rem;
    padding-bottom: 60px;
  }

  .product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(250px, 100%), 1fr));
    gap: 1rem;
    padding: 1rem;
  }

  .product {
    border: 1px solid #ccc;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    background-color: white;
    border-radius: 8px;
  }

  .product.normal {
    /* Default size, no changes needed */
  }

  .product.medium {
    transform: scale(1.05);
    z-index: 1;
  }

  .product.large {
    transform: scale(1.1);
    z-index: 2;
  }

  .product.xl {
    transform: scale(1.15);
    z-index: 3;
  }

  .product.glow {
    box-shadow: 10px 5px 5px  rgba(0, 255, 0, 0.5);
  }

  .product:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-5px);
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
    font-size: 1.2rem;
  }

  .product p {
    margin: 0.5rem 0;
    font-size: 0.9rem;
  }

  .price {
    font-weight: bold;
    color: var(--primary-color);
  }

  .score {
    font-weight: bold;
    color: #4CAF50;
  }

  .search-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
  }

  .search-container.large input {
    font-size: 1.5rem;
    padding: 1rem;
  }

  .search-container.large button {
    font-size: 1.5rem;
    padding: 1rem 1.5rem;
  }

  .search-container.bottom {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: white;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
  }

  input {
    width: 100%;
    max-width: 600px;
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

  .loading-animation {
    width: 50px;
    height: 50px;
    border: 5px solid #f3f3f3;
    border-top: 5px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-top: 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .glowing-circle {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    margin-left: 10px;
    animation: glow 1.5s infinite alternate;
  }

  .glowing-circle.connected {
    background-color: #4CAF50;
    box-shadow: 0 0 10px #4CAF50;
  }

  .glowing-circle.disconnected {
    background-color: #F44336;
    box-shadow: 0 0 10px #F44336;
  }

  .toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
  }

  .toast {
    background-color: #333;
    color: white;
    padding: 12px 20px;
    border-radius: 4px;
    margin-bottom: 10px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    font-size: 14px;
  }

  .toast.success {
    background-color: #4CAF50;
  }

  .toast.error {
    background-color: #F44336;
  }

  .toast.info {
    background-color: #2196F3;
  }

  @keyframes glow {
    from {
      opacity: 0.5;
    }
    to {
      opacity: 1;
    }
  }
</style>