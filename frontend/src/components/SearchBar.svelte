<script>
     import { createEventDispatcher } from 'svelte';
  import FeedbackWave from './FeedbackWave.svelte';
  import LoadingAnimation from './LoadingAnimation.svelte';


  export let searchTerm;
  export let isWebSocketConnected;
  export let isRecording;
  export let isLoading;
  export let position;

  let inputRef;


  const dispatch = createEventDispatcher();


  function startVoiceSearch() {
    // Function logic for starting voice search
  }

  function handleKeyDown(event) {
    if (event.key === "Enter") {
      dispatch('enterPress');
    }
  }
</script>

<div class="search-container {position}">
  <input type="text" bind:this={inputRef} bind:value={searchTerm} placeholder="Search products..." on:keydown={handleKeyDown} /><button on:click={startVoiceSearch}>🎤</button>
  <button on:click={startVoiceSearch}>🎤</button>
  <div class="glowing-circle {isWebSocketConnected ? 'connected' : 'disconnected'}"></div>
  {#if isRecording}
    <FeedbackWave />
  {/if}
  {#if isLoading}
    <LoadingAnimation />
  {/if}
</div>

<style>
  .search-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
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
    font-size: 0.8rem;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
    border-radius: 4px;
  }

  button:hover {
    background-color: var(--secondary-color);
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

  @keyframes glow {
    from {
      opacity: 0.5;
    }
    to {
      opacity: 1;
    }
  }
</style>
