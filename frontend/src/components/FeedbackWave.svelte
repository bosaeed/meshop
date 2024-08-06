<div class="feedback-wave"></div>

<style>
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
