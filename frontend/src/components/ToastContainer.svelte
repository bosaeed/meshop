<script>
     import { fly } from 'svelte/transition';
  export let toasts;
</script>

<div class="toast-container">
  {#each toasts as toast (toast.id)}
    <div class="toast {toast.type}" transition:fly="{{ y: 50, duration: 300 }}">
      {toast.message}
    </div>
  {/each}
</div>

<style>
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
</style>
