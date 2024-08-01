<!-- meshop/frontend/src/components/Header.svelte -->
<script>
    import { Link } from "svelte-routing";
  </script>
  
  <header>
    <nav>
      <Link to="/">Home</Link>
      <!-- <Link to="/products">Products</Link> -->
      <!-- <Link to="/cart">Cart</Link> -->
    </nav>
  </header>
  
  <style>
    header {
      background-color: #f4f4f4;
      padding: 1rem;
    }
  
    nav {
      display: flex;
      gap: 1rem;
    }
  </style>