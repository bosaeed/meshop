<script>
    export let message = "";
    export let type = "info"; // "success", "error", "info"
    export let show = false;
    export let duration = 0; // Duration in milliseconds before hiding the billboard

    let showTimeout= null;
    $:message,duration, showTimeout,set_timeout()

    function set_timeout() {
        if(showTimeout){
            clearTimeout(showTimeout)
        }
        if(duration > 0) {
            showTimeout= setTimeout(() => show = false, duration);
        }
    }
  </script>
  
  {#if show}
    <div class="billboard {type}">
      <pre>{message}</pre>
    </div>
  {/if}
  
  <style>
    .billboard {
      position: fixed; /* Attach to the top */
      top: 0;
      left: 0;
      width: 100%;
      padding: 0.2rem;
      background-color: #b0ca66; /* Light gray default */
      color: #333;
      text-align: center;
      z-index: 100; /* Ensure it's on top */
      transition: background-color 0.3s ease;
    }
  
    .billboard.success {
      background-color: #4CAF50; /* Green for success */
      color: white;
    }
  
    .billboard.error {
      background-color: #F44336; /* Red for error */
      color: white;
    }
  
    .billboard pre { /* Style for preformatted JSON message */
      white-space: pre-wrap;
      font-size: 1.2rem;
      margin-top: 0.2rem;
    }
  </style>