<!-- meshop/frontend/src/components/Header.svelte -->
<script>
    import { Link } from "svelte-routing";
  </script>
  
  <header>
    <nav>
      <Link to="/">Home</Link>
    </nav>
  </header>
  
  <style>
    header {
      background-color: var(--primary-color);
      padding: 1rem;
    }
  
    nav {
      display: flex;
      gap: 1rem;
    }
  
  </style>